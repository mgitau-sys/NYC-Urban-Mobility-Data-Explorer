import json
import os
import sqlite3
import clean
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TRIP_COLS = ["trip_id", "vendor_id", "pu_location_id", "dropoff_datetime", "pickup_datetime", "do_location_id",
             "rate_code_id", "payment_type_id", "passenger_count", "trip_distance",
             "tip_amount", "tolls_amount", "fare_amount", "extra", "mta_tax", "improvement_surcharge", "congestion_surcharge", "airport_fee", "total_amount" ]
FEATURE_COLS = ["trip_id", "duration_min", "speed_mph", "fare_per_mile", "tip_pct", "pickup_hour", "pickup_dow", "time_bucket"]
def main():
    ap = argparse.ArgumentParser(description="Build taxi.db from TLC trip data")
    ap.add_argument("--trips", required=True, help="yellow_tripdata")
    ap.add_argument("--lookup", default=os.path.join(ROOT, "data", "taxi_zone_lookup.csv"))
    ap.add_argument("--geojson", default=os.path.join(ROOT, "data", "taxi_zones.geojson"))
    ap.add_argument("--db", default=os.path.join(ROOT, "taxi.db"))
    ap.add_argument("--max-rows", type=int, default=0, help="maximum clean trip to  keep")
    args = ap.parse_args()
    print("1/5 Reading Zones(CSV + GeoJSON)..")
    zones, geo = clean.load_zones(args.lookup, args.geojson)
    with open(os.path.join(ROOT, "data", "zones_clean.geojson"), "w")as file:
        json.dump(geo,file)
        
    print("2/5 Reading and Cleaning..")
    raw = clean.load_trips(args.trips)
    valid = set(zones["location_id"]) - clean.UNKNOWN_ZONES
    kept, excluded, report = clean.clean_trips(raw, valid)
    
    if args.max_rows and len (kept) > args.max_rows:
        kept = kept.sample(args.max_rows, random_state=42).sort_values("pickup_datetime")
        report["sample_down_to"] = args.max_rows
        
    print("3/5 Feature Engineering...")
    kept = clean.add_features(kept)
    kept.insert(0, "trip_id", range(1, len(kept) +1))
     
    print("4/5 Databese Writing...")
    if os.path.exists(args.db):
        os.remove(args.db)
    con = sqlite3.connect(args.db)
    with open(os.path.join(HERE, "schema.sql")) as schema_file:
        con.executescript(schema_file.read())
    con.execute("PRAGMA foreign_keys = ON")
    
    con.executemany("INSERT INTO rate_codes VALUES (?,?)", clean.RATE_CODES.items())
    con.executemany("INSERT INTO vendors VALUES (?,?)", clean.VENDORS.items())
    con.executemany("INSERT INTO payment_types VALUES (?,?)", clean.PAYMENT_TYPES_ITEMS())
    zones.to_sql("zones", con, if_exists="append", index=False)
    kept[TRIP_COLS].to_sql("trips", con, if_exists="append", index=False, chunksize=50000 )
    kept[FEATURE_COLS].to_sql("trip_features", con, if_exists="append", index=False, chunksize=50000)
    excluded.to_sql("excluded_records", con, if_exists="append", index=False, chunksize=50000)
    con.commit()
    con.close()
    
    print("5/5 Saving the cleaning report..")
    with open(os.path.join(ROOT, "docs", "cleaning_report.json"), "w") as file:
        json.dump(report, file, indent=2)
    
    print(json.dumps(report, indent=2))
    print(f"\nDone -> {args.db}")
    
    if __name__ == "__main__":
        main()


