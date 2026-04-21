import os
import shutil
import sys
from random import Random
import time
import requests
import PIL
import json
import ast
from pathlib import Path

# Support running this file directly (python path/to/pipeline.py)
# by making backend/src importable as the package root.
if __package__ in (None, ""):
    src_root = Path(__file__).resolve().parents[2]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

from models.ground.rest import EOWriteRequest
from models.query import query_by_area
from models.Space.earth import Earth
from models.ground import scheduling_component


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
            Earth.update_metadata(mapping[passes[i]], new_state="QUEUED")


    def process_products(self, mapping):
        processed_dir = DATA_DIR / "processed"
        processed_dir.mkdir(exist_ok=True, parents=True)

        while len(self.images_in_processing) > 0:
            image = self.images_in_processing.pop(0)
            pass_id = image.split("_")[-1].split(".")[0]
            Earth.update_metadata(mapping[pass_id], new_state="PROCESSING")
            print(f"Queue length {len(self.images_in_processing)}")
            print(f"Processing {image}...")
            # time.sleep(Random().randint(1, 5))
            new_path = shutil.move(DATA_DIR / f"incoming/{image}", processed_dir / image)

            Earth.update_metadata(mapping[pass_id], new_state="COMPLETED", new_image_path=new_path)
            print(f"Finished processing {image}!")

    def archive_products(self, images: list[str], mapping: dict[str, EOWriteRequest]):
        archive_dir = DATA_DIR / "archive"
        catalog_dir = DATA_DIR / "catalog"
        archive_dir.mkdir(exist_ok=True, parents=True)
        catalog_dir.mkdir(exist_ok=True, parents=True)
        for image in images:
            print(f"Archiving {image}...")
            pass_id = image.split("_")[-1].split(".")[0]
            metadata = mapping[pass_id]
            image_path = archive_dir / metadata.satellite_id / metadata.area_name / metadata.generated_at / image
            image_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(DATA_DIR / f"processed/{image}", image_path)
            Earth.update_metadata(metadata, new_state="ARCHIVED", new_image_path=str(image_path))
            
            catalog_format = {
                "eo_product_id": metadata.eo_product_id,
                "satellite_id": metadata.satellite_id,
                "area_name": metadata.area_name,
                "timestamp": metadata.generated_at,
                "archive_path": str(image_path)
            }
            with open(catalog_dir / f"{metadata.eo_product_id}.catalog.json", "w") as f:
                json.dump(catalog_format, f, indent=4)



    def run(self):
        passes, mapping = self.generate_products()
        self.ingest_products(os.listdir(DATA_DIR / "incoming"), passes, mapping)
        self.process_products(mapping)
        self.archive_products(os.listdir(DATA_DIR / "processed"), mapping)

        response = query_by_area(mapping[passes[0]].area_name)
        print(f"Found {len(response)} results:")
        for result in response:
            print(f"{result['eo_product_id']} → {result['archive_path']}")

def main():
    pipeline = EOPipeline()
    pipeline.run()

if __name__ == "__main__":
    main()