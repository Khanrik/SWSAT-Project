""""
Lab 4 — Scheduling & Flight Plan

Follows the cosntraints
- No overlap
- No duration below `MIN_DURATION_MINUTES`
- Sorted by the decision rule **Earliest finish time first**

Constraints must be evaluated in this exact order:

Concurrency capacity (antenna limits)
Temporal spacing constraint
Cumulative downlink budget
Maximum passes per day
The first violated constraint determines the rejection reason.

Do not reorder constraints.

The order influences the scheduling outcome.
"""

import json
from datetime import datetime
import pandas as pd

POLICY_PATH = "backend/src/models/input1_policy_medium.json"
MIN_DURATION_MINUTES = 8

def load_policies(filename):
    with open(filename, "r") as f:
        data = json.load(f)

    return data["antenna_count_by_station"], \
        data["min_spacing_minutes_by_station"], \
        data["max_downlink_mb_per_day"], \
        data["max_passes_per_day"]

def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def duration_minutes(start, end):
    return (end - start).total_seconds() / 60


def load_passes(filename):
    with open(filename, "r") as f:
        data = json.load(f)

    return data["satellite_id"], data["date"], data["passes"]


def filter_valid_passes(passes, antenna_limits, min_spacing_minutes, cum_downlink_budget, max_passes_per_day):
    """
    You must:
    - Reject passes if above antenna limits (concurrency)
    - Reject passes if above temporal spacing constraint
    - Reject passes if above cumulative downlink budget
    - Reject passes if above maximum passes per day
    
    the first violated constraint determines the rejection reason. Do not reorder constraints.
    """

    valid = []
    station_counter = {
        "GS1": 0,
        "GS2": 0,
        "GS3": 0
    }

    for p in passes:
        start = parse_time(p["start_time"])
        end = parse_time(p["end_time"])
        station = p["station_id"]
        downlink_mb = p["downlink_mb"]

        if antenna_limits[station] <= station_counter[station]:
            continue
        station_counter[station] += 1
        
        if duration_minutes(start, end) <= min_spacing_minutes[station]:
            continue
        if downlink_mb > cum_downlink_budget:
            continue
        
 
        
        valid.append(p)

    return valid


def schedule_passes(passes, max_passes_per_day):
    """
    You must:
    - Choose and implement ONE decision rule
    - Ensure no overlapping passes
    - Respect MAX_PASSES_PER_DAY
    """
    scheduled = []

    df = pd.DataFrame(passes)
    df["end_time"] = pd.to_datetime(df["end_time"])
    df = df.sort_values(by="end_time")
    df["end_time"] = df["end_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    parsed = json.loads(df.to_json(orient="records"))

    scheduled.append(parsed[0])
    for p in parsed[1:]:
        if len(scheduled) == max_passes_per_day:
            break
        if parse_time(p["start_time"]) <= parse_time(scheduled[-1]["end_time"]):
            continue
        scheduled.append(p)

    return scheduled


def generate_flight_plan(satellite_id, date, scheduled_passes):
    """
    Output format must match specification.
    """
    flight_plan = {
        "satellite_id": satellite_id,
        "date": date,
        "scheduled_passes": scheduled_passes
    }

    return flight_plan


def main():
    satellite_id, date, passes = load_passes("official_passes.json")
    antenna_limits, min_spacing_minutes, cum_downlink_budget, max_passes_per_day = load_policies(POLICY_PATH)

    valid_passes = filter_valid_passes(passes, antenna_limits, min_spacing_minutes, cum_downlink_budget, max_passes_per_day)
    scheduled = schedule_passes(valid_passes, max_passes_per_day=max_passes_per_day)

    flight_plan = generate_flight_plan(
        satellite_id,
        date,
        scheduled
    )

    with open("flight_plan.json", "w") as f:
        json.dump(flight_plan, f, indent=2)

    print("Flight plan generated.")


if __name__ == "__main__":
    main()
