from pathlib import Path
import requests
import shutil

API_URL = "http://127.0.0.1:8000"
DATA_DIR = Path(__file__).parent.parent.parent / "framework/data"

def reset_eo_products():
    proccessed_dir = DATA_DIR / "processed"
    incoming_dir = DATA_DIR / "incoming"
    archive_dir = DATA_DIR / "archive"
    catalog_dir = DATA_DIR / "catalog"
    enhanced_dir = DATA_DIR / "enhanced"

    if proccessed_dir.exists():
        shutil.rmtree(proccessed_dir)
    if incoming_dir.exists():
        shutil.rmtree(incoming_dir)
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    if catalog_dir.exists():
        shutil.rmtree(catalog_dir)
    if enhanced_dir.exists():
        shutil.rmtree(enhanced_dir)
    requests.delete(f"{API_URL}/eo_products/delete_all")

def main():
    reset_eo_products()

if __name__ == "__main__":
    main()