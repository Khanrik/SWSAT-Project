import os
import shutil
import sys
import requests
import json
import ast
from pathlib import Path

# Support running this file directly (python path/to/pipeline.py)
# by making backend/src importable as the package root.
if __package__ in (None, ""):
    src_root = Path(__file__).resolve().parents[2]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

from models.ground.processing_pipeline import catalog_product, ProcessingPipeline
from models.ground.rest import EOWriteRequest
from models.query import query_by_area
from models.Space.earth import Earth


API_URL = "http://127.0.0.1:8000"
DATA_DIR = Path("backend/framework/data")

class EOPipeline:
    images_in_processing = []
    working_dir = os.getcwd()

    def generate_products(self):
        incoming_dir = DATA_DIR / "incoming"
        incoming_dir.mkdir(exist_ok=True, parents=True)

        response = requests.get(f"{API_URL}/flight_plan", timeout=30)

        if response.headers.get("Content-Type") == "application/json":
            data = response.json()
            # only proceed if data exists
            if data:
                passes = requests.get(f"{API_URL}/flight_plan/{data[0]}/scheduled_passes", timeout=30).json()
                passes = ast.literal_eval(passes[0])
            else:
                print("No flight plan data returned")
        else:
            print("Invalid response:", response.text)

        passes_product_mapping = {}

        print(passes)
        for pass_id in passes:
            image_data = Earth.give_data(True)
            image_data = image_data.convert("L")  # or "RGB"

            image_path = incoming_dir / f"EO-Sen1A_image_{pass_id}.png"
            print(f"Generated image for pass {pass_id} at {image_path}")
            image_data.save(image_path)
            eo_product_data = Earth.generate_metadata(pass_id, image_path=image_path)
            passes_product_mapping[pass_id] = eo_product_data
        
        return passes, passes_product_mapping


    def ingest_products(self, images, passes, mapping):
        for image in images:
            self.images_in_processing.append(image)
        for i in range(len(passes)):
            Earth.update_metadata(mapping[passes[i]], updated_values={"processing_state": "QUEUED"})


    def process_products(self, mapping):
        processed_dir = DATA_DIR / "processed"
        processed_dir.mkdir(exist_ok=True, parents=True)

        while len(self.images_in_processing) > 0:
            image = self.images_in_processing.pop(0)
            pass_id = image.split("_")[-1].split(".")[0]
            Earth.update_metadata(mapping[pass_id], updated_values={"processing_state": "PROCESSING"})
            print(f"Queue length {len(self.images_in_processing)}")
            print(f"Processing {image}...")
            # time.sleep(Random().randint(1, 5))
            new_path = shutil.move(DATA_DIR / f"incoming/{image}", processed_dir / image)

            Earth.update_metadata(mapping[pass_id], updated_values={"processing_state": "PROCESSED", "image_path": str(new_path)})
            print(f"Finished processing {image}!")

    def archive_products(self, images: list[str], mapping: dict[str, EOWriteRequest]):
        archive_dir = DATA_DIR / "archive"
        archive_dir.mkdir(exist_ok=True, parents=True)
        for image in images:
            print(f"Archiving {image}...")
            pass_id = image.split("_")[-1].split(".")[0]
            metadata = mapping[pass_id]
            image_path = archive_dir / metadata.satellite_id / metadata.area_name / metadata.generated_at / image
            image_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(DATA_DIR / f"processed/{image}", image_path)
            catalog_dict = {
                "eo_product_id": metadata.eo_product_id,
                "satellite_id": metadata.satellite_id,
                "area_name": metadata.area_name,
                "generated_at": metadata.generated_at,
                "archive_path": str(image_path),
                "enhanced_image_path": None,
                "quality_score": None,
                "brightness": None,
                "contrast": None,
                "is_visible": None,
                "is_anomaly": None,
                "priority": None,
                "meaning": None
            }
            catalog_product(catalog_dict)
    
    def run(self):
        passes, mapping = self.generate_products()
        self.ingest_products(os.listdir(DATA_DIR / "incoming"), passes, mapping)
        self.process_products(mapping)
        self.archive_products(os.listdir(DATA_DIR / "processed"), mapping)
        
        # Run processing pipeline to enhance images and update metadata
        catalog_dir = DATA_DIR / "catalog"
        processing_pipeline = ProcessingPipeline()
        print("Processing and enhancing archived products...")
        processing_pipeline.run(catalog_dir)
        print("Processing complete. Database and catalog files updated.")
        
        response = query_by_area(mapping[passes[0]].area_name)
        print(f"Found {len(response)} results:")
        for result in response:
            print(f"{result['eo_product_id']} → {result['archive_path']}")

def main():
    pipeline = EOPipeline()
    pipeline.run()

if __name__ == "__main__":
    main()