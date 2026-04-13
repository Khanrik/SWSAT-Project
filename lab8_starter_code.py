#Lab8 Starter Code
#--------------------------
import os
import json
import time
from pathlib import Path

# =============================
# CONFIGURATION
# =============================

BASE_DIR = Path("SWSAT-Project") #change to your folder name 
INCOMING_DIR = BASE_DIR / "object_store" / "incoming"
PROCESSED_DIR = BASE_DIR / "processed"
METADATA_DIR = BASE_DIR / "metadata"
LOGS_DIR = BASE_DIR / "logs"

NUM_PRODUCTS = 10
PROCESSING_DELAY = 1  # seconds


# =============================
# SETUP FUNCTIONS
# =============================

def setup_directories():
    """
    Create required folder structure.
    """
    # TODO:
    # Create all directories using mkdir(parents=True, exist_ok=True)
    pass


# =============================
# TASK 1: GENERATE PRODUCTS
# =============================

def generate_products():
    """
    Create EO products in incoming/ with metadata.
    """
    products = []

    for i in range(1, NUM_PRODUCTS + 1):
        eo_id = f"EO-S1A-2026-03-24-{i:03d}"
        file_name = f"{eo_id}.png"

        product = {
            "eo_product_id": eo_id,
            "satellite_id": "Sentinel-1A",
            "pass_id": eo_id,
            "timestamp": "2026-03-24T10:25:00Z",
            "area_name": "Aarhus, Denmark",
            "file_name": file_name,
            "size_mb": 50,
            "processing_state": "GENERATED"
        }

        # TODO:
        # 1. Create a placeholder file in incoming/
        # Hint: write_text("dummy data")

        # TODO:
        # 2. Save metadata as JSON in metadata/

        products.append(product)

    print(f"Generated {len(products)} EO products")
    return products


# =============================
# TASK 2: INGEST PRODUCTS
# =============================

def ingest_products(products, queue):
    """
    Move products into queue and update state.
    """

    for product in products:

        # TODO:
        # Change state to QUEUED

        # TODO:
        # Add product to queue

        print(f"[INGEST] {product['eo_product_id']} -> QUEUED")

    print(f"Queue length: {len(queue)}")


# =============================
# TASK 3: WORKER
# =============================

def process_product(product):
    """
    Process a single EO product.
    """

    # TODO:
    # Update state to PROCESSING

    print(f"[WORKER] Processing {product['eo_product_id']}")

    # simulate processing time
    time.sleep(PROCESSING_DELAY)

    # TODO:
    # Move file from incoming/ to processed/
    # Hint: use os.rename() or shutil.move()

    # TODO:
    # Update state to COMPLETED

    print(f"[WORKER] Completed {product['eo_product_id']}")


# =============================
# TASK 4–6: PIPELINE EXECUTION
# =============================

def run_pipeline(products):
    queue = []

    # Ingest first (burst)
    ingest_products(products, queue)

    visible_count = 0

    print("\n--- START PROCESSING ---\n")

    # Process queue
    while queue:
        product = queue.pop(0)  # FIFO

        process_product(product)

        visible_count += 1

        print(f"Queue length: {len(queue)}")
        print(f"Visible images: {visible_count}")


# =============================
# MAIN
# =============================

def main():
    setup_directories()

    products = generate_products()

    run_pipeline(products)


if __name__ == "__main__":
    main()