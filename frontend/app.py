import json
import os
from pathlib import Path
from flask import Flask, render_template, request, send_file, abort

app = Flask(__name__)

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "backend/framework/data"
CATALOG_DIR = DATA_DIR / "catalog"
ARCHIVE_DIR = DATA_DIR / "archive"


# =========================
# TASK 1: LOAD CATALOG from Lab 9
# =========================
def load_catalog():
    """
    Read all catalog JSON files and return a list of EO products.
    """
    products = []

    for element in [CATALOG_DIR / f for f in os.listdir(CATALOG_DIR)]:
        with open(element,"r") as file:
            products.append(json.load(file))
            

    return products


# =========================
# TASK 2: FILTERING
# =========================
def apply_filters(products, area_name="", satellite_id="", date=""):
    
    filtered = []
    for element in products:
        if area_name != "" and element["area_name"] != area_name :
            continue
        if satellite_id != "" and element["satellite_id"] != satellite_id:
            continue
        if date != "" and element["timestamp"] != date:
            continue
        
        filtered.append(element)

    return filtered


# =========================
# TASK 3: SELECT PRODUCT
# =========================
def get_selected_product(products, selected_id):
    for product in products:
        if(product["eo_product_id"] == selected_id):
            return product

    if len(products) != 0:
        return products[0]
    return None


# =========================
# TASK 4: MAIN DASHBOARD
# =========================
@app.route("/") #API endpoint mapping
def index():

    products = load_catalog()

    # Read filters from URL
    area_name = request.args.get("area_name", "").strip()
    satellite_id = request.args.get("satellite_id", "").strip()
    date = request.args.get("date", "").strip()
    selected_id = request.args.get("selected_id", "").strip()


    products = apply_filters(products, area_name, satellite_id, date)

    selected_product = get_selected_product(products, selected_id)

    return render_template(
        "index.html",
        products=products,
        selected_product=selected_product,
        area_name=area_name,
        satellite_id=satellite_id,
        date=date
    )


# =========================
# TASK 5: IMAGE ENDPOINT
# =========================
@app.route("/image/<eo_product_id>") #API endpoint mapping
def serve_image(eo_product_id):

    products = load_catalog()

    for product in products:
        if(product["eo_product_id"] == eo_product_id):
            path = WORKSPACE / product["archive_path"]
            if(os.path.exists(path)):
                
                return send_file(path)
    abort(404)


# =========================
# OPTIONAL: SIMPLE API
# =========================
@app.route("/api/products") #API endpoint mapping
def api_products():
    """
    Optional: return JSON data
    """
    products = load_catalog()
    return products


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)