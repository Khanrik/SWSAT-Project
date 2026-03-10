import sqlite3
import json

PATH = "framework/data/passes.db"
PASSES = "backend/src/models/input1_passes_medium.json"
FLIGHT_PLAN = "backend/src/models/flight_plan.json"

def main():
    
    db = sqlite3.connect(PATH)

    cursor = db.cursor()

    with open(PASSES, "r") as f:
        passes_data = json.load(f)
        
    with open(FLIGHT_PLAN, "r") as f:
        flight_plan_data = json.load(f)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Passes (
            pass_id TEXT PRIMARY KEY,
            station_id TEXT,
            start_time TEXT,
            end_time TEXT,
            downlink_mb REAL,
            priority_score REAL
        )
        """
    )
    

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS FlightPlan (
            flightplan_id TEXT PRIMARY KEY,
            Scheduled_passes TEXT,
            Rejected_passes TEXT
        )
        """
    )
    
    pass_rows = [
        (
            entry["pass_id"],
            entry["station_id"],
            entry["start_time"],
            entry["end_time"],
            entry["downlink_mb"],
            entry["priority_score"],
        )
        for entry in passes_data.get("passes", [])
    ]

    cursor.executemany(
        """
        INSERT OR REPLACE INTO Passes
        (pass_id, station_id, start_time, end_time, downlink_mb, priority_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        pass_rows,
    )

    scheduled_ids = [entry["pass_id"] for entry in flight_plan_data["scheduled_passes"]]
    rejected_with_reason = [
        {
            "pass_id": item["pass"]["pass_id"],
            "reason": item["reason"],
        }
        for item in flight_plan_data["rejected_passes"]
    ]

    cursor.execute(
        """
        INSERT INTO FlightPlan (flightplan_id, Scheduled_passes, Rejected_passes)
        VALUES (?, ?, ?)
        """,
        (
            flight_plan_data["flightplan_id"],
            json.dumps(scheduled_ids),
            json.dumps(rejected_with_reason),
        ),
    )

    db.commit()
    db.close()

    print("vickning chips til 14kr lets gooo!!")


if __name__ == "__main__":
    main()