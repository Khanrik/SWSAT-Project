from PIL import Image, ImageEnhance
import json
import glob
from pathlib import Path
import numpy as np
from tqdm import tqdm
import sys

# Support running this file directly (python path/to/pipeline.py)
# by making backend/src importable as the package root.
if __package__ in (None, ""):
    src_root = Path(__file__).resolve().parents[2]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

from models.Space.earth import Earth

DATA_DIR = Path("backend/framework/data")

def catalog_product(metadata: dict):
    catalog_dir = DATA_DIR / "catalog"
    catalog_dir.mkdir(exist_ok=True, parents=True)
    with open(catalog_dir / f"{metadata['eo_product_id']}.catalog.json", "w") as f:
        json.dump(metadata, f, indent=4)

class ProcessingPipeline:
    def __init__(self, batch_size = 5):
        self.batch_size = batch_size

        
    def run(self, metadata_dir: Path):
        data = self.get_metadata(metadata_dir)
        batches = self.split_into_batches(data)
        
        results=[]
        for batch in tqdm(batches):
            results.extend(self.process_batch(batch))

        
        
        Earth.update_metadata(metadata, updated_values={"processing_state": "ARCHIVED", "image_path": str(image_path)})
        
        
    
    def get_metadata(self,path):

        data = []
        for filename in glob.glob(path + "/*.json"):
            with open(filename,"r") as metadata: 
                data.append(json.load(metadata))
        return data
    
    def split_into_batches(self, data):
        N = len(data)
        batches = []

        for i in range(0, N, self.batch_size):
            batch = data[i:i + self.batch_size]
            batches.append(batch)

        return batches

    def process_batch(self, batch: list[dict]):
        processed_batch = []

        for metadata in batch:
            image_path = Path(metadata["archive_path"])
            enhanced_image_path = image_path.parents[4] / "enhanced" / f"enhanced_{image_path.name}"
            enhanced_image_path.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(metadata["archive_path"]) as image:
                enhanced_image = self.enhance_product(image)
                enhanced_image.save(enhanced_image_path)

                score = self.score_product(enhanced_image)
                
            metadata["enhanced_image_path"] = str(enhanced_image_path)
            for key in metadata.keys():
                if key in score.keys():
                    metadata[key] = score[key]
            processed_batch.append(metadata)

        return processed_batch

    def enhance_product(self, image: Image.ImageFile):
        return ImageEnhance.Contrast(image).enhance(1.5)

    def score_product(self, image: Image.ImageFile):
        score = {
            "quality_score": 0,
            "brightness": 0,
            "contrast": 0,
            "is_visible": False,
            "is_anomaly": False,
            "priority": 0,
        }
        image_array = np.array(image)
        score["brightness"] = image_array.mean() / 255.0
        score["contrast"] = image_array.std() / 255.0
        score["quality_score"] = ((0.5 - (np.abs((score["brightness"]-0.5))))*2 + score["contrast"]) / 2
        score["is_visible"] = score["brightness"] > 0.1 or score["contrast"] > 0.1
        score["is_anomaly"] = score["brightness"] > 0.9 or score["contrast"] > 0.9
        priority = 0
        if score["is_anomaly"]:
            priority += 1
        score["priority"] 
        return score
