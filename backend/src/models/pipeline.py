import os
import shutil
from random import Random
import time
import requests
import PIL

from earth import Earth

class EOPipeline:
    images_in_processing = []
    working_dir = os.getcwd()
    def generate_products(self):
        # TODO: create EO products and save to incoming/
        os.makedirs("incoming", exist_ok=True)
        for i in range(10):
            image_data = Earth.give_data()
            image_data.save(f"incoming/EO-Sen1A_image_{i}.png")

    def ingest_products(self, images):
        # TODO: move products into queue and update state
        for image in images:
            self.images_in_processing.append(image)


    def process_product(self):
        # TODO: simulate processing and move files
        while len(self.images_in_processing) > 0:
            image = self.images_in_processing.pop(0)
            print(f"Queue length {len(self.images_in_processing)}")
            print(f"Processing {image}...")
            time.sleep(Random().randint(1, 5))
            os.makedirs("processed", exist_ok=True)
            shutil.move(f"incoming/{image}", f"processed/")
            print(f"Finished processing {image}!")

    def run(self):
        # TODO: control pipeline flow
        self.generate_products()
        self.ingest_products(os.listdir("incoming"))
        self.process_product()

if __name__ == "__main__":
    pipeline = EOPipeline()
    pipeline.run()