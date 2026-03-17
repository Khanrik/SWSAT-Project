from fastapi import FastAPI
from .database import Database

app = FastAPI()
db = Database()

#endpoints
@app.post("/schedule")
def create_flightplan():
    db.write()
    return {"message": "Passes created successfully"}

@app.get("/flight_plan/{flightplan_id}/scheduled_passes")
def read_schedule(flightplan_id: str):
    return db.read("scheduled_passes", flightplan_id)

@app.get("/flight_plan/{flightplan_id}/rejected_passes")
def read_rejected(flightplan_id: str):
    return db.read("rejected_passes", flightplan_id)

@app.get("/passes/{pass_id}")
def read_passes(pass_id: str):
    return db.read("passes", pass_id)