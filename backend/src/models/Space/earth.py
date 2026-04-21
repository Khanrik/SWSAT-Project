from PIL import Image
from pathlib import Path
import numpy as np
import math




import random
import requests
import datetime

try:
    from ..ground.rest import EOWriteRequest
except ImportError:
    from ground.rest import EOWriteRequest

API_URL = "http://127.0.0.1:8000"

class Earth:

    def give_data(funny = True):
        

        if funny:
            data = fun()

            data = (data - data.min()) / (data.max() - data.min() + 1e-8)
            data = (data * 255).astype(np.uint8)
            
        else:
            width, height = 256, 256
            data = np.random.randint(0, 256, (width, height), dtype=np.uint8)

        
        img = Image.fromarray(data, mode="L")
        # comment in line below for debugging
        # img.show()
        return img
        
    def generate_metadata(pass_id, processing = "GENERATED", product_id = None, image_path = "idk"):
        time = datetime.datetime.now().strftime("%m-%d-%Y_%H-%M-%S.%f")
        product_id = product_id or "SCH-" + time
        
        Locations = ["Aarhus Harbor","Aarhus University","Den Permanente","Marselisborg Harbor","Hørret","Ajstrup Strand","Egå","Aarhus Center"]
        rand = random.randint(0,len(Locations)-1)
        location = Locations[rand]

        params = EOWriteRequest(
            eo_product_id = product_id,
            flightplan_id = "EO_IMAGE",
            pass_id = pass_id,
            satellite_id = "Sentinel-1A",
            area_name = location,
            generated_at = time,
            image_path = str(image_path),
            image_width = 256,
            image_height = 256,
            processing_state = processing
        )
        
        requests.post(f"{API_URL}/eo_products", json=params.model_dump(), timeout=30)

        return params
    
    def update_metadata(metadata: EOWriteRequest, new_state: str = None, new_image_path: str = None):
        """Update the metadata of an EO product in place"""
        if new_state is not None:
            metadata.processing_state = new_state
        if new_image_path is not None:
            metadata.image_path = str(new_image_path)
        requests.post(f"{API_URL}/eo_products", json=metadata.model_dump(), timeout=30)


def gradient(ix, iy):
    # fast integer hash
    h = (ix * 1836311903) ^ (iy * 2971215073)
    h = (h << 13) ^ h
    h = (h * (h * h * 15731 + 789221) + 1376312589) & 0xffffffff

    angle = (h / 0xffffffff) * 2 * math.pi
    return math.cos(angle), math.sin(angle)

def lerp(a, b, x):
    """Linear interpolation."""
    return a + x * (b - a)

def fade(t):
    """Smoothstep interpolation."""
    return t * t * t * (t * (t * 6 - 15) + 10)

def perlin(x, y, grid_size=8):
    x0, y0 = int(x // grid_size), int(y // grid_size)
    x1, y1 = x0 + 1, y0 + 1

    dx = x / grid_size - x0
    dy = y / grid_size - y0

    g00 = gradient(x0, y0)
    g10 = gradient(x1, y0)
    g01 = gradient(x0, y1)
    g11 = gradient(x1, y1)

    dot00 = g00[0]*dx + g00[1]*dy
    dot10 = g10[0]*(dx-1) + g10[1]*dy
    dot01 = g01[0]*dx + g01[1]*(dy-1)
    dot11 = g11[0]*(dx-1) + g11[1]*(dy-1)

    u, v = fade(dx), fade(dy)

    value = lerp(
        lerp(dot00, dot10, u),
        lerp(dot01, dot11, u),
        v
    )

    # normalize to [0, 1]
    return (value / math.sqrt(2) + 1) * 0.5


def fun():
    
    size = 25
    resolution = 250

    octaves = 5

    seed = np.random.rand(2,1)

    x = np.linspace(0,size,resolution)
    y = x

    grid = np.zeros((resolution, resolution))
    sx = float(seed[0, 0] * 100)
    sy = float(seed[1, 0] * 100)

    x_scaled = x * 0.25
    y_scaled = y * 0.25

    for i in range(resolution):
        for j in range(resolution):

            x_val = sx+x[i]
            y_val = sy+y[j]
            mountain = perlin((sx+x_scaled[i]), (sy+y_scaled[j])) 
            for octave in range(1,octaves):
                eps = 1e-5

                noise = perlin(x_val * octave, y_val * octave)
                dx = perlin((x_val + eps) * octave, y_val * octave) - noise
                dy = perlin(x_val * octave, (y_val + eps) * octave) - noise

                gradient0 = dx / eps
                gradient1 = dy / eps

                mag = np.abs(np.sqrt(gradient0**2 + gradient1**2))

                if(octave < 3 and noise > mountain):
                    noise = mountain

                grid[i,j] += noise * 1/octave * (np.exp(-mag*2) * 1/octave)
    return grid




if __name__ == "__main__":
    Earth.give_data(True)