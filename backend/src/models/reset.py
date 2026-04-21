from pathlib import Path
import requests
import shutil

API_URL = "http://127.0.0.1:8000"

def reset_eo_products():
    proccessed_dir = Path.cwd() / "processed"
    incoming_dir = Path.cwd() / "incoming"
    archive_dir = Path.cwd() / "archive"
    catalog_dir = Path.cwd() / "catalog"
    if proccessed_dir.exists():
        shutil.rmtree(proccessed_dir)
    if incoming_dir.exists():
        shutil.rmtree(incoming_dir)
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    if catalog_dir.exists():
        shutil.rmtree(catalog_dir)
    requests.delete(f"{API_URL}/eo_products/delete_all")

def main():
    reset_eo_products()

if __name__ == "__main__":
    main()