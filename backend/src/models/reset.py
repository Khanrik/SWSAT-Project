from pathlib import Path
import requests
import shutil

API_URL = "http://127.0.0.1:8000"

def reset_eo_products():
    proccessed_dir = Path.cwd() / "processed"
    incoming_dir = Path.cwd() / "incoming"
    if proccessed_dir.exists():
        shutil.rmtree(proccessed_dir)
    if incoming_dir.exists():
        shutil.rmtree(incoming_dir)
    requests.delete(f"{API_URL}/eo_products/delete_all")

def main():
    reset_eo_products()

if __name__ == "__main__":
    main()