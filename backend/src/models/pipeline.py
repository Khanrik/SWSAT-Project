import os
import shutil
from random import Random
import time
import requests
import PIL
import json
import ast

try:
    from .rest import EOWriteRequest
except ImportError:
    from rest import EOWriteRequest

from earth import Earth

API_URL = "http://127.0.0.1:8000"


class EOPipeline:
    images_in_processing = []
    working_dir = os.getcwd()

    def generate_products(self):
        os.makedirs("incoming", exist_ok=True)

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
            image_path = f"incoming/EO-Sen1A_image_{pass_id}.png"
            image_data.save(image_path)
            eo_product_id = Earth.generate_metadata(pass_id, image_path=image_path)
            passes_product_mapping[pass_id] = eo_product_id
        
        return passes, passes_product_mapping


    def ingest_products(self, images, passes, mapping):
        for image in images:
            self.images_in_processing.append(image)
        for i in range(len(passes)):
            Earth.generate_metadata(passes[i], processing="QUEUED", product_id=mapping[passes[i]])


    def process_product(self, mapping):
        while len(self.images_in_processing) > 0:
            image = self.images_in_processing.pop(0)
            pass_id = image.split("_")[-1].split(".")[0]
            Earth.generate_metadata(pass_id, processing="PROCESSING", product_id=mapping[pass_id])
            print(f"Queue length {len(self.images_in_processing)}")
            print(f"Processing {image}...")
            time.sleep(Random().randint(1, 5))
            os.makedirs("processed", exist_ok=True)
            new_path = shutil.move(f"incoming/{image}", f"processed/")

            Earth.generate_metadata(pass_id, processing="COMPLETED", product_id=mapping[pass_id], image_path = new_path)
            print(f"Finished processing {image}!")

    def run(self):
        passes, mapping = self.generate_products()
        self.ingest_products(os.listdir("incoming"), passes, mapping)
        self.process_product(mapping)

if __name__ == "__main__":
    pipeline = EOPipeline()
    pipeline.run()