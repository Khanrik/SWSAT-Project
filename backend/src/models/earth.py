from PIL import Image
from pathlib import Path
import numpy as np

import random
import requests
import datetime

try:
    from .rest import EOWriteRequest
except ImportError:
    from rest import EOWriteRequest

API_URL = "http://127.0.0.1:8000"

class Earth:

    def give_data(self):
        width, height = 256, 256
        data = np.random.randint(0, 256, (width, height), dtype=np.uint8)
        img = Image.fromarray(data)
        # comment in line below for debugging
        # img.show()
        return img
        
    def generate_metadata(self,pass_id):

        time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        params = EOWriteRequest(
            eo_product_id = "SCH-" + time,
            flightplan_id = "EO_IMAGE",
            pass_id = pass_id,
            satellite_id = "Sentinel-1A",
            area_name = "Aarhus, Denmark",
            generated_at = time,
            image_path = "idk",
            image_width = 256,
            image_height = 256,
            processing_state = "GENERATED"
        )
        
        requests.post(f"{API_URL}/eo_outputs", json=params.model_dump(), timeout=30)


if __name__ == "__main__":
    earth = Earth()
    earth.give_data()