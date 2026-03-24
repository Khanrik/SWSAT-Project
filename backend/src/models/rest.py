from fastapi import FastAPI

try:
    from .database import Database
except ImportError:
    from database import Database

app = FastAPI(title="SWSAT Flight Plan API", 
              version="1.0",
              description="API for managing satellite communication passes and flight plans.")
db = Database()

#endpoints
@app.post("/schedule")
def create_flightplan():
    """Endpoint to create a flight plan based on the passes data."""
    db.write()
    return {"message": "Passes created successfully"}

@app.get("/flight_plan/{flightplan_id}/scheduled_passes")
def read_schedule(flightplan_id: str):
    """Endpoint to read scheduled passes for a given flight plan."""
    return db.read("scheduled_passes", flightplan_id)

@app.get("/flight_plan/{flightplan_id}/rejected_passes")
def read_rejected(flightplan_id: str):
    """Endpoint to read rejected passes for a given flight plan."""
    return db.read("rejected_passes", flightplan_id)

@app.get("/passes/{pass_id}")
def read_passes(pass_id: str):
    """Endpoint to read a specific pass."""
    return db.read("passes", pass_id)