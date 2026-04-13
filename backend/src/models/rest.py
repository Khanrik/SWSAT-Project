from typing import Any

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

try:
    from .database import Database
except ImportError:
    from database import Database

app = FastAPI(title="SWSAT Flight Plan API", 
              version="1.0",
              description="API for managing satellite communication passes and flight plans.")

class PassWriteRequest(BaseModel):
    pass_id: str
    satellite: str
    start_time: str
    end_time: str
    ground_station: str

class FlightPlanWriteRequest(BaseModel):
    flightplan_id: str
    Scheduled_passes: list[str]
    Rejected_passes: list[dict[str, Any]]

class EOWriteRequest(BaseModel):
    eo_product_id: str
    flightplan_id: str
    pass_id: str
    satellite_id: str
    area_name: str
    generated_at: str
    image_path: str
    image_width: int
    image_height: int
    processing_state: str

#endpoints
@app.post("/schedule")
def create_local_flightplan():
    """Endpoint to create a flight plan based on the locally stored passes data."""
    with Database() as db:
        db.write_local_files()
    return {"message": "Passes created successfully"}

@app.post("/passes")
def create_pass(payload: PassWriteRequest):
    """Create or replace one pass entry."""
    with Database() as db:
        db.write("Passes", [payload.model_dump()])
    return {
        "message": "Pass written successfully",
        "pass_id": payload.pass_id,
    }

@app.post("/flight_plan")
def create_flight_plan(payload: FlightPlanWriteRequest):
    """Create or replace one flight plan entry."""
    with Database() as db:
      db.write("FlightPlan", [payload.model_dump()])
    return {
        "message": "Flight plan written successfully",
        "flightplan_id": payload.flightplan_id,
    }

@app.post("/eo_outputs")
def create_eo(payload: EOWriteRequest):
    """Create or replace one EO entry."""
    with Database() as db:
        db.write("eo_outputs", [payload.model_dump()])
    return {
        "message": "EO written successfully",
        "eo_product_id": payload.eo_product_id,
    }

@app.get("/flight_plan/{flightplan_id}/scheduled_passes")
def read_schedule(flightplan_id: str):
    """Endpoint to read scheduled passes for a given flight plan."""
    with Database() as db:
        return db.read("scheduled_passes", flightplan_id)

@app.get("/flight_plan")
def get_flight_plan_ids():
    """Endpoint to read all flight plan IDs."""
    with Database() as db:
        return db.read("scheduled_passes")
    
@app.get("/flight_plan/{flightplan_id}/rejected_passes")
def read_rejected(flightplan_id: str):
    """Endpoint to read rejected passes for a given flight plan."""
    with Database() as db:
        return db.read("rejected_passes", flightplan_id)

@app.get("/passes/{pass_id}")
def read_passes(pass_id: str):
    """Endpoint to read a specific pass."""
    with Database() as db:
        return db.read("passes", pass_id)
    
@app.get("/passes")
def get_pass_ids(pass_id: str):
    """Endpoint to read all pass IDs."""
    with Database() as db:
        return db.read("passes")
    
@app.get("/")
def read_root():
    """Redirects to the API documentation."""
    return RedirectResponse(url="/docs", status_code=307)