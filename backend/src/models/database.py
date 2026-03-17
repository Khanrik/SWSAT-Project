import json
import sqlite3
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "framework" / "data" / "passes.db"
PASSES = Path(__file__).resolve().with_name("input1_passes_medium.json")
FLIGHT_PLAN = Path(__file__).resolve().with_name("flight_plan.json")

class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(DB_PATH)
        self.cursor = db.cursor()
        self.cursor.execute(
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

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS FlightPlan (
                flightplan_id TEXT PRIMARY KEY,
                Scheduled_passes TEXT,
                Rejected_passes TEXT
            )
            """
        )

    def read(self, endpoint: Literal["scheduled_passes", "rejected_passes", "passes"], identifier: str):
        data = {}

        match endpoint:
            case "scheduled_passes":
                data = self.cursor.execute(
                    f"""
                    SELECT Scheduled_passes
                    FROM FlightPlan
                    WHERE flightplan_id = '{identifier}'
                    """)
                
            case "rejected_passes":
                data = self.cursor.execute(
                    f"""
                    SELECT Rejected_passes
                    FROM FlightPlan
                    WHERE flightplan_id = '{identifier}'
                    """)
            case "passes":
                data = self.cursor.execute(
                    f"""
                    SELECT *
                    FROM Passes
                    WHERE pass_id = '{identifier}'
                    """)

        # print(data.fetchall())
        return data.fetchall()

    def write(self):
        with open(PASSES, "r") as f:
            passes_data = json.load(f)
        
        with open(FLIGHT_PLAN, "r") as f:
            flight_plan_data = json.load(f)
        
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

        self.cursor.executemany(
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

        self.cursor.execute(
            """
            INSERT OR REPLACE INTO FlightPlan (flightplan_id, Scheduled_passes, Rejected_passes)
            VALUES (?, ?, ?)
            """,
            (
                flight_plan_data["flightplan_id"],
                json.dumps(scheduled_ids),
                json.dumps(rejected_with_reason),
            ),
        )

        self.db.commit()
        self.db.close()

        print(f"Populated database: {DB_PATH}")
        print(f"Inserted {len(pass_rows)} passes and 1 flight plan.")

if __name__ == "__main__":
    db = Database()
    print("after read" + str(db.read("M01", "1ddfb7e7-34ab-4158-9454-ee21bb8d93b5")))