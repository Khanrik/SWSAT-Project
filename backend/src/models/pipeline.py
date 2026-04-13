import os
import shutil
from random import Random
import time
import requests
import PIL
import json

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
            else:
                print("No flight plan data returned")
        else:
            print("Invalid response:", response.text)

    
        for i in range(len(passes)):
            image_data = Earth.give_data()
            image_data = image_data.convert("L")  # or "RGB"
            image_data.save(f"incoming/EO-Sen1A_image_{i}.png")
            Earth.generate_metadata(passes[i])
            

    def ingest_products(self, images):
        for image in images:
            self.images_in_processing.append(image)


    def process_product(self):
        while len(self.images_in_processing) > 0:
            image = self.images_in_processing.pop(0)
            print(f"Queue length {len(self.images_in_processing)}")
            print(f"Processing {image}...")
            time.sleep(Random().randint(1, 5))
            os.makedirs("processed", exist_ok=True)
            
            shutil.move(f"incoming/{image}", f"processed/")

            print(f"Finished processing {image}!")

    def run(self):
        self.generate_products()
        self.ingest_products(os.listdir("incoming"))
        self.process_product()

if __name__ == "__main__":
    pipeline = EOPipeline()
    pipeline.run()