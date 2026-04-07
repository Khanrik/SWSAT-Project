import json
import sqlite3
from pathlib import Path
from typing import Literal, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "framework" / "data" / "passes.db"
PASSES = Path(__file__).resolve().with_name("input1_passes_medium.json")
FLIGHT_PLAN = Path(__file__).resolve().with_name("flight_plan.json")

class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
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

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS eo_products (
                    eo_product_id TEXT PRIMARY KEY,
                    flightplan_id TEXT NOT NULL,
                    pass_id TEXT NOT NULL,
                    satellite_id TEXTV NOT NULL,
                    area_name TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    image_width INTEGER NOT NULL,
                    image_height INTEGER NOT NULL,
                    processing_state TEXT NOT NULL)
                """
            )

    def get_flightplan_ids(self):
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
            data = cursor.execute(
                """
                SELECT flightplan_id
                FROM FlightPlan
                """
            )
            return [row[0] for row in data.fetchall()]

    def get_pass_ids(self):
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
            data = cursor.execute(
                """
                SELECT pass_id
                FROM Passes
                """
            )
            return [row[0] for row in data.fetchall()]

    def read(self, endpoint: Literal["scheduled_passes", "rejected_passes", "passes"], identifier: str | None = None):
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()

            match endpoint:
                case "scheduled_passes":
                    if not identifier:
                        return self.get_flightplan_ids()
                    data = cursor.execute(
                        """
                        SELECT Scheduled_passes
                        FROM FlightPlan
                        WHERE flightplan_id = ?
                        """,
                        (identifier,),
                    )


                case "rejected_passes":
                    if not identifier:
                        return self.get_flightplan_ids()
                    data = cursor.execute(
                        """
                        SELECT Rejected_passes
                        FROM FlightPlan
                        WHERE flightplan_id = ?
                        """,
                        (identifier,),
                    )

                case "passes":
                    if not identifier:
                        return self.get_pass_ids()
                    data = cursor.execute(
                        """
                        SELECT *
                        FROM Passes
                        WHERE pass_id = ?
                        """,
                        (identifier,),
                    )
            return data.fetchall()
        
    def write(self, table: Literal["Passes", "FlightPlan", "eo_outputs"], data: List[dict[str, Any]]):
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
            match table:
                case "Passes":
                    formatted_data = [
                        (
                            pass_data["pass_id"],
                            pass_data["station_id"],
                            pass_data["start_time"],
                            pass_data["end_time"],
                            pass_data["downlink_mb"],
                            pass_data["priority_score"],
                        )
                        for pass_data in data
                    ]
                    cursor.executemany(
                        """
                        INSERT OR REPLACE INTO Passes
                        (pass_id, station_id, start_time, end_time, downlink_mb, priority_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        formatted_data,
                    )

                case "FlightPlan":
                    formatted_data = [
                        (
                            flight_data["flightplan_id"],
                            json.dumps(flight_data["Scheduled_passes"]),
                            json.dumps(flight_data["Rejected_passes"])
                        )
                        for flight_data in data
                    ]
                    cursor.executemany(
                        """
                        INSERT OR REPLACE INTO FlightPlan
                        (flightplan_id, Scheduled_passes, Rejected_passes)
                        VALUES (?, ?, ?)
                        """,
                        formatted_data,
                    )

                case "eo_outputs":
                    formatted_data = [
                        (
                            eo_data["eo_product_id"],
                            eo_data["flightplan_id"],
                            eo_data["pass_id"],
                            eo_data["satellite_id"],
                            eo_data["area_name"],
                            eo_data["generated_at"],
                            eo_data["image_path"],
                            eo_data["image_width"],
                            eo_data["image_height"],
                            eo_data["processing_state"],
                        )
                        for eo_data in data
                    ]
                    cursor.executemany(
                        """
                        INSERT OR REPLACE INTO eo_products
                        (eo_product_id, flightplan_id, pass_id, satellite_id, area_name, generated_at, image_path, image_width, image_height, processing_state)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        formatted_data,
                    )


    def write_local_files(self):
        with open(PASSES, "r") as f:
            passes_data: dict = json.load(f)
        
        with open(FLIGHT_PLAN, "r") as f:
            flight_plan_data: dict = json.load(f)
        
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

        scheduled_ids = [entry["pass_id"] for entry in flight_plan_data["scheduled_passes"]]
        rejected_with_reason = [
            {
                "pass_id": item["pass"]["pass_id"],
                "reason": item["reason"],
            }
            for item in flight_plan_data["rejected_passes"]
        ]

        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO Passes
                (pass_id, station_id, start_time, end_time, downlink_mb, priority_score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                pass_rows,
            )

            cursor.execute(
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

        print(f"Populated database: {DB_PATH}")
        print(f"Inserted {len(pass_rows)} passes and 1 flight plan.")

if __name__ == "__main__":
    db = Database()
    print("What was read: " + str(db.read("scheduled_passes", "1ddfb7e7-34ab-4158-9454-ee21bb8d93b5")))

def __enter__(self):
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    pass