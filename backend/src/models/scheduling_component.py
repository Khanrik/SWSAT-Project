""""
Lab 4 — Scheduling & Flight Plan

Follows the cosntraints
- No overlap
- No duration below `MIN_DURATION_MINUTES`
- Sorted by the decision rule **Earliest start time first**

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
import uuid

POLICY_PATH = "backend/src/models/input1_policy_medium.json"

def load_policies(filename):
    with open(filename, "r") as f:
        data = json.load(f)

    return  data["antenna_count_by_station"], \
            data["min_spacing_minutes_by_station"], \
            data["max_downlink_mb_per_day"], \
            data["max_passes_per_day"]

def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")


def duration_minutes(start, end):
    return (end - start).total_seconds() / 60


def load_passes(filename):
    with open(filename, "r") as f:
        data = json.load(f)

    return data["passes"]


def capacity_valid(candidate, valid_passes, antenna_limit):
    overlap_count = 0

    for p in valid_passes:
        if p["station_id"] != candidate["station_id"]:
            continue

        if parse_time(p["start_time"]) < parse_time(candidate["end_time"]) and parse_time(p["end_time"]) > parse_time(candidate["start_time"]):
            overlap_count += 1
    
    return overlap_count < antenna_limit


def spacing_valid(candidate, valid_passes, min_spacing_minutes):
    valid = True
    for p in valid_passes:
        if p["station_id"] != candidate["station_id"]:
            continue

        if parse_time(p["start_time"]) < parse_time(candidate["end_time"]) and parse_time(p["end_time"]) > parse_time(candidate["start_time"]):
            continue

        if(not (abs(duration_minutes(parse_time(p["start_time"]), parse_time(candidate["end_time"]))) >= min_spacing_minutes)):
           valid = False

        if(not (abs(duration_minutes(parse_time(candidate["start_time"]), parse_time(p["end_time"]))) >= min_spacing_minutes)):
            valid = False

    return valid

def downlink_budget_valid(candidate, valid_passes, max_downlink_budget):
    cumulative_downlink = sum(p["downlink_mb"] for p in valid_passes) + candidate["downlink_mb"]
    return cumulative_downlink <= max_downlink_budget


def max_passes_valid(valid_passes, max_passes_per_day):
    return len(valid_passes) < max_passes_per_day


def filter_valid_passes(passes, 
                        antenna_limits, 
                        min_spacing_minutes, 
                        max_downlink_budget, 
                        max_passes_per_day,
                        validation_dict):
    """
    You must:
    - Reject passes if above antenna limits (concurrency)
    - Reject passes if above temporal spacing constraint
    - Reject passes if above cumulative downlink budget
    - Reject passes if above maximum passes per day
    
    the first violated constraint determines the rejection reason. Do not reorder constraints.
    """
    valid = []
    rejected = []
    

    
    for p in passes:
        if not capacity_valid(p, valid, antenna_limits[p["station_id"]]):
            validation_dict["CAPACITY_CONFLICT"] += 1
            rejection = {"pass": p, "reason": "CAPACITY_CONFLICT"}
            rejected.append(rejection)

            continue
        
        if not spacing_valid(p, valid, min_spacing_minutes[p["station_id"]]):
            validation_dict["SPACING_VIOLATION"] += 1
            rejection = {"pass": p, "reason": "SPACING_VIOLATION"}
            rejected.append(rejection)
            continue

        if not downlink_budget_valid(p, valid, max_downlink_budget):
            validation_dict["BUDGET_VIOLATION"] += 1
            rejection = {"pass": p, "reason": "BUDGET_VIOLATION"}
            rejected.append(rejection)
            continue
        
        if not max_passes_valid(valid, max_passes_per_day):
            validation_dict["MAX_PASSES_LIMIT"] += 1
            rejection = {"pass": p, "reason": "MAX_PASSES_LIMIT"}
            rejected.append(rejection)
            continue
        
        valid.append(p)

    return valid, validation_dict,rejected


def generate_flight_plan(scheduled_passes, rejected_passes, generation_time: datetime):
    """
    Output format must match specification.
    """
    flight_plan = {
        "flightplan_id": str(uuid.uuid4()),
        "generation_time": generation_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scheduled_passes": scheduled_passes,
        "rejected_passes": rejected_passes
    }

    return flight_plan


def main():
    passes = load_passes("backend/src/models/input1_passes_medium.json")
    antenna_limits, min_spacing_minutes, max_downlink_budget, max_passes_per_day = load_policies(POLICY_PATH)

    validation_dict = {
        "CAPACITY_CONFLICT":0,
        "SPACING_VIOLATION":0,
        "BUDGET_VIOLATION":0,
        "MAX_PASSES_LIMIT":0
    }
        
    sorted_passes = sorted(passes, key=lambda p: (-p["priority_score"], p["start_time"], p["pass_id"]))
    valid_passes, validation_dict, rejected_passes  = filter_valid_passes(  sorted_passes, 
                                                                            antenna_limits, 
                                                                            min_spacing_minutes, 
                                                                            max_downlink_budget,
                                                                            max_passes_per_day,
                                                                            validation_dict)

    flight_plan = generate_flight_plan(
        valid_passes,
        rejected_passes,
        datetime.now()
    )

    with open("backend/src/models/flight_plan.json", "w") as f:
        json.dump(flight_plan, f, indent=2)

    print("Flight plan generated.")
    print(f"MAX_PASSES_LIMIT: {validation_dict['MAX_PASSES_LIMIT']}")
    print(f"CAPACITY_CONFLICT: {validation_dict['CAPACITY_CONFLICT']}")
    print(f"SPACING_VIOLATION: {validation_dict['SPACING_VIOLATION']}")
    print(f"BUDGET_VIOLATION: {validation_dict['BUDGET_VIOLATION']}")


if __name__ == "__main__":
    main()
