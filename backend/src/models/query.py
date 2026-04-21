from pathlib import Path
import json

CATALOG_DIR = Path("backend/framework/data/catalog")

def query_by_area(area_name: str):
    """Query archived EO products by area name."""
    results = []
    for catalog_file in CATALOG_DIR.glob("*.catalog.json"):
        with open(catalog_file) as f:
            metadata = json.load(f)
            if metadata["area_name"] == area_name:
                results.append(metadata)
    return results