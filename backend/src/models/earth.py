from PIL import Image
from pathlib import Path
import numpy as np
import math




import random
import requests
import datetime

try:
    from .rest import EOWriteRequest
except ImportError:
    from rest import EOWriteRequest

API_URL = "http://127.0.0.1:8000"

class Earth:

    def give_data():
        funny = True

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
        
    # TODO: something something call
    def generate_metadata(pass_id):

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

def gradient(ix, iy):
    random.seed(ix * 1836311903 ^ iy * 2971215073)
    angle = random.random() * 2 * math.pi
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
    min = 0
    max = 25
    count = 150

    octaves = 5

    seed = np.random.rand(2,1)

    x = np.linspace(min,max,count)
    y = x

    grid = np.zeros((count, count))
    grid1 = np.zeros((count, count))
    for i in range(count):
        for j in range(count):

            mountain = perlin((+x[i])* 0.25, ((seed[1]*100)+y[j])*0.25) 
            for octave in range(1,octaves):
                eps = 1e-5

                noise = perlin(((seed[0]*100)+x[i]) * octave, ((seed[1]*100)+y[j]) * octave)
                dx = perlin((((seed[0]*100)+x[i]) + eps) * octave, ((seed[1]*100)+y[j]) * octave) - noise
                dy = perlin(((seed[0]*100)+x[i]) * octave, (((seed[1]*100)+y[j]) + eps) * octave) - noise

                gradient0 = dx / eps
                gradient1 = dy / eps

                mag = np.abs(np.sqrt(gradient0**2 + gradient1**2))

                if(octave < 3):
                    if(noise > mountain):
                        noise = mountain

                grid[i,j] += noise * 1/octave * (np.exp(-mag*2) * 1/octave)
    return grid




if __name__ == "__main__":
    earth = Earth()
    earth.give_data()