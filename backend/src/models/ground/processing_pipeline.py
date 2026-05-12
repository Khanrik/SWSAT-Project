from PIL import Image, ImageEnhance, ImageFile
import json
import glob
import sklearn as sk
from pathlib import Path
import numpy as np
from tqdm import tqdm
import sys
import requests
import matplotlib.pyplot as plt

# Support running this file directly (python path/to/pipeline.py)
# by making backend/src importable as the package root.
if __package__ in (None, ""):
    src_root = Path(__file__).resolve().parents[2]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

from models.Space.earth import Earth
from models.ground.rest import EOWriteRequest

API_URL = "http://127.0.0.1:8000"

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
        
        scores = []

        for processed in results:
            scores.append([processed["brightness"],processed["contrast"]])
        
        # Perform k-means clustering on quality scores
        labels, centers = self.k_means(scores)
        values = scores
        scores = []
        for processed in results:
            scores.append(processed["quality_score"])

        scores = np.array(scores)
        labels = np.array(labels)

        data = np.column_stack((scores, labels))

        unique_labels = []
        unique_scores = []

        for i in range(len(data)):
            if data[i][1] not in unique_labels:
                unique_labels.append(data[i][1])
                unique_scores.append(data[i][0])

        unique_labels = np.array(unique_labels)
        unique_scores = np.array(unique_scores)

        data = np.column_stack((unique_scores, unique_labels))

        sorted_data = data[np.argsort(data[:, 0])[::-1]]

        label_meanings = {
            int(sorted_data[0][1]): "high_quality",
            int(sorted_data[1][1]): "medium_quality",
            int(sorted_data[2][1]): "low_quality"
        }

        #plot the kmeans with the label driving the color and in 2d of brightness and contrast
        _, ax = plt.subplots()

        values = np.array(values)
        labels = np.array(labels)
        centers = np.array(centers)

        for cluster_id in np.unique(labels):

            mask = labels == cluster_id

            scatter = ax.scatter(
                values[mask, 0],   # brightness
                values[mask, 1],   # contrast
                label=label_meanings[cluster_id]
            )

            color = scatter.get_facecolor()[0]
        
            ax.scatter(
            centers[cluster_id, 0],
            centers[cluster_id, 1],
            color=color,
            marker='x',
            s=200,
            linewidths=2
            )

        ax.set_xlabel("Brightness")
        ax.set_ylabel("Contrast")
        ax.set_title("K-Means Clustering of Image Quality")
        ax.grid()
        ax.legend()

        plt.show()

        resolution = 255
        grid = np.zeros((resolution, resolution))

        for i in range(resolution):
            for j in range(resolution):

                bounded_brightness = i / resolution
                bounded_contrast = j / resolution

                ranged_brightness = 0.5 - abs(bounded_brightness - 0.5) * 2

                grid[i, j] = ((ranged_brightness + bounded_contrast) / 2)

        plt.imshow(
            grid,
            cmap="gray",
            interpolation="nearest",
            origin="lower"   # flips the y-axis
        )
        ticks = np.linspace(0, 255, 6)
        plt.yticks(ticks)
        plt.xticks(ticks)

        plt.xlabel("Contrast")
        plt.ylabel("Brightness")

        plt.colorbar(label="Pixel Value")

        plt.show()


        i = 0
        for metadata in results:
            metadata["labels"] = str(labels[i])
            metadata["centers"] = json.dumps(centers[labels[i]].tolist())
            metadata["meaning"] = label_meanings[int(labels[i])]
            i += 1


        # Update catalog JSON files with processed results
        for processed_metadata in results:
            # Update catalog JSON file
            catalog_path = Path(metadata_dir) / f"{processed_metadata['eo_product_id']}.catalog.json"
            with open(catalog_path, "w") as f:
                json.dump(processed_metadata, f, indent=4)
        
        # Sync all catalog files to database
        self.update_database_from_catalog(metadata_dir)

    
    def update_database_from_catalog(self, catalog_dir: Path):
        """Read all catalog JSON files and update only the enhanced fields in the database."""
        from models.ground.database import Database
        
        catalog_files = list(Path(catalog_dir).glob("*.catalog.json"))
        db = Database()
        
        for catalog_file in catalog_files:
            with open(catalog_file, "r") as f:
                enhanced_data = json.load(f)
            
            eo_product_id = enhanced_data.get("eo_product_id", "")
            
            # Query database for existing record
            existing_records = db.read("eo_products", eo_product_id)
            if not existing_records:
                print(f"Warning: No existing record found for {eo_product_id}")
                continue
            
            existing_record = existing_records[0]
            
            # Database column order from schema:
            # eo_product_id, flightplan_id, pass_id, satellite_id, area_name, generated_at,
            # image_path, image_width, image_height, processing_state, quality_score,
            # brightness, contrast, is_visible, is_anomaly, priority, enhanced_image_path
            
            eo_request = EOWriteRequest(
                eo_product_id=existing_record[0],
                flightplan_id=existing_record[1],
                pass_id=existing_record[2],
                satellite_id=existing_record[3],
                area_name=existing_record[4],
                generated_at=existing_record[5],
                image_path=existing_record[6],
                image_width=existing_record[7],
                image_height=existing_record[8],
                processing_state=existing_record[9],
                # Update only the enhanced fields from JSON
                quality_score=float(enhanced_data.get("quality_score", existing_record[10])),
                brightness=float(enhanced_data.get("brightness", existing_record[11])),
                contrast=float(enhanced_data.get("contrast", existing_record[12])),
                is_visible=enhanced_data.get("is_visible", bool(existing_record[13])),
                is_anomaly=enhanced_data.get("is_anomaly", bool(existing_record[14])),
                priority=int(enhanced_data.get("priority", existing_record[15])),
                enhanced_image_path=enhanced_data.get("enhanced_image_path", existing_record[16] if len(existing_record) > 16 else ""),
                labels=enhanced_data.get("labels", existing_record[17] if len(existing_record) > 17 else ""),
                centers=enhanced_data.get("centers", existing_record[18] if len(existing_record) > 18 else ""),
                meaning=enhanced_data.get("meaning",existing_record[19] if len(existing_record) > 19 else "")
            )
            
            requests.post(f"{API_URL}/eo_products", json=eo_request.model_dump(), timeout=30)
        
        
    
    
    def get_metadata(self, path: Path):
        data = []
        base = Path(path)
        for filepath in base.glob("*.json"):
            with open(filepath, "r") as metadata:
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

                score = self.score_product(enhanced_image) # Need 2D array for sklearn
            metadata["enhanced_image_path"] = str(enhanced_image_path)
            for key in metadata.keys():
                if key in score.keys():
                    metadata[key] = score[key]
            processed_batch.append(metadata)
        


        return processed_batch

    def enhance_product(self, image: ImageFile):
        return ImageEnhance.Contrast(image).enhance(1.5)

    def score_product(self, image: ImageFile):
        score = {
            "quality_score": 0,
            "brightness": 0,
            "contrast": 0,
            "is_visible": False,
            "is_anomaly": False,
            "priority": 0,
        }
        image_array = np.array(image)
        score["brightness"] = float(image_array.mean() / 255.0)
        score["contrast"] = float(image_array.std() / 255.0)
        score["quality_score"] = float(((0.5 - (np.abs(score["brightness"]-0.5)))*2 + score["contrast"]) / 2)
        score["is_visible"] = bool(score["brightness"] > 0.1 or score["contrast"] > 0.1)
        score["is_anomaly"] = bool(score["brightness"] > 0.9 or score["contrast"] > 0.9)
        priority = 0
        qs = score["quality_score"]
        if score["is_anomaly"]:
            priority -= qs*10
        else:
            priority += qs*10
        score["priority"] = priority
        return score
    
    def k_means(self,score):
        kmeans = sk.cluster.KMeans(3).fit(score)
        return kmeans.labels_,kmeans.cluster_centers_