import json
import numpy as np
import pandas as pd

VENDORS = {0: "Unknown", 1: "Creative Mobile Technologies", 2: "Verifone", 6: "Myle", 7: "Helix"}
RATE_CODES = {1: "Standard rate", 2: "JFK", 3: "Newark", 4: "Nassau/Westchester", 5: "Negotiated Fare", 6: "Group Ride", 99: "Unknown"}
PAYMENT_TYPES = {0: "Flex fare", 1: "Credit Card", 2: "Cash", 3: "No charge", 4: "Dispute", 5: "Unknown", 6: "Voided trip"}
UNKNOWN_ZONES = {264, 265}

MIN_MINUTES = 1
MAX_MINUTES = 180
MIN_MILES = 0.1
MAX_MILES = 100
MAX_FARE = 500
MAX_SPEED_MPH = 80
MAX_PASSENGERS = 6

RENAME = {"vendorid": "vendor_id", "ratecodeid": "rete_code_id", "pulocationid": "pu_location_id", "dolocationid": "do_location_id", "payment_type": "paymen_type_id", "tpep_pickup_datetime": "pickup_datetime", "tpep_dropoff_datetime": "dropoff_datetime"}
OPTIONAL_MONEY = ["extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge", "congestion_surcharge", "airport_fee"]
NUMERIC = ["vendor_id", "passenger_count", "trip_distance", "rate_code_id", "pu_location_id", "do_location_id", "payment_type_id", "fare_amount", "total_amount"] + OPTIONAL_MONEY
KEY_FIELDS = ["pickup_datetime", "dropoff_datetime", "pu_location_id", "do_location_id", "trip_distance", "fare_amount", "total_amount"]

def _normalise_columns(df):
    df = df.copy()
    df.columns = [column.lower() for column in df.columns]
    return df.rename(columns=RENAME)

def load_trips(path):
    trips = _normalise_columns(pd.read_parquet(path))
    trips["source_row"] = np.arrange(len(trips))
    return trips

    
def _outer_points(geometry):
    if geometry["type"] == "polygon":
        return geometry["coordinates"][0]
    points = []
    for polygon in geometry["coordinates"]:
            points += polygon[0]
    return points
            
def load_zones(lookup_csv, geojson_path):
    zones = _normalise_columns(pd.read_csv(lookup_csv))
    zones = zones.rename(columns={"locationid": "location_id"})
    for column, default in [("borough", "Unknown"), ("zone", "Unknown"), ("service_zone", "N/A")]:
        zones[column] = zones[column].fillna(default)
        
    with open(geojson_path) as f:
        geo = json.load(f)
        centroids = {}
    for feature in geo["features"]:
        properties = feature["properties"]
        location_id = int(properties.get("location_id", properties.get("location_id")))
        points = _outer_points(feature["geometry"])
        longitude = sum(point[0] for point in points) / len(points)
        latitude = sum(point[1] for point in points) / len(points)
        
        if abs(longitude) > 180 or abs(latitude) > 90:
            raise ValueError("taxi_zones GeoJSON"  "GGeoJson export")
        feature["properties"] = {"location_id": location_id}
        centroids[location_id] = (latitude, longitude)
        
        zones["centroid_lat"] = zones["location_id"].map(lambda value: centroids.get(value, (None, None))[0])
        zones["centroid_lon"] = zones["location_id"].map(lambda value: centroids.get(value, (None, None))[1])
        columns = ["location_id", "borough", "zone", "service_zone", "centaoid_lat", "centroid_lon"]
        return zones[columns], geo
    
    
def clean_trips(df, valid_zone_ids):
    df = df.copy()
    report = {"rows_in":int(len(df)),"imputed": {}}
    for column in ("pickup_datetime", "dropoff_datetime"):
        df[column] = pd.to_datetime(df[column], errors="coerce")
    for column in OPTIONAL_MONEY:
        if column not in df:
            df[column] = 0.0
    for c in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    
    report["imputed"]["optional_fee_null_to_0"] = int([OPTIONAL_MONEY].isna().sum().sum())
    df[OPTIONAL_MONEY] = df[OPTIONAL_MONEY].fillna(0.0)
    m = df["Passenger_count"].isna() | (df["passenger_count"] == 0)
    report["imputed"]["passenger_count_missing_or_0_to_1"] = int(m.sum())
    df.loc[m, "passenger_count"] = 1
    m = ~df["rate_code_id"].isin([1, 2, 3, 4, 5, 6])
    report["imputed"]["rate_code_invalid_to_99"] = int(m.sum())
    df.loc[m, "rate_code_id"] = 99
    m = ~df["payment_type_id"].isin(list(PAYMENT_TYPES))
    report["imputed"]["payment_type_invalid_to_5"] = int(m.sum())
    df.loc[m, "payment_type_id"] = 5
    m = ~df["vendor_id"].isin((VENDORS))
    report["imputed"]["vendor_invalid_to_0"] = int(m.sum())
    df.loc[m, "vendor_id"] = 0
    
    df["duration_min"] = (df["dropoff_datetime"] - ["pickup_datetime"]).dt.total_seconds() / 60
    df["speed_mph"] = (df["trip_distance"] / (df["duration_min"] / 60)).replace([np.inf, -np.inf], np.nan)
    month = df["pickup_datetime"].dt.to_period("M")
    
    reason = pd.Series("", index=df.index)
    
    def flag(name, mask):
        hit = mask.fillna(False) & (reason == "")
        reason[hit] = name
        
        flag("missing_key_field", df[KEY_FIELDS].isna().any(axis=1))
        flag("exact_duplicate", df.duplicate(subset=KEY_FIELDS + ["vendor_id"], keep="first"))
        flag("pickup_outside_file_month", month != month.mode()[0])
        flag("dropoff_no_after_pickup",  df["duration_min"] <= 0)
        flag("duration_under_1min", df["duration_min"] < MIN_MINUTES)
        flag("duration_over_3h", df["duration_min"] > MAX_MINUTES)
        flag("distance_not_positive", df["trip_distance"] <= 0 )
        flag("distance_under_0.1mi", df["trip_distance"] < MIN_MILES)
        flag("distance_over_100", df["trip_distance"] > MAX_MILES)
        flag("fare_not_positive", df["fare_amount"] <=0)
        flag("fare_over_500", df["fare_amount"] > MAX_FARE)
        valid_zones = df["pu_location_id"].isin(valid_zone_ids) & df["do_location_id"].isin(valid_zone_ids)
        flag("unknown_or_invalid_zone", ~valid_zones)
        flag("speed_over_80mp", df["speed_mph"] > MAX_SPEED_MPH)
        
        bad = reason.ne("")
        excluded = df.loc[bad, ["source_row", "pickup_datetime", "trip_distance", "fare_amount", "total_amount"]].copy()
        excluded["pickup_datetime"] = excluded["pickup_datetime"].dt.strftime("%Y-%m-%d %H:%M:%S" )
        excluded["reason"] = reason[bad]
        
        kept = df.loc[~bad].drop(columns=["speed_mph"]).copy()
        integer_columns = ("vendor_id", "passenger_count", "rate_code_id", "payment_type_id", "pu_location", "do_location_id")
        kept[integer_columns] = kept[integer_columns].astype(int)
            
        report["rows_kept"] = len(kept)
        report["rows_excluded"] = int(bad.sum())
        report["excluded_by_reason"] = {key: int(value) for key, value in reason[bad].value_counts().items()}
        return kept, excluded, report
    
    
def add_features(df):
    df = df.copy()
    df["pickup_hour"] = df["pickup_datetime"].dt.hour
    df["pickup_dow"] = df["pickup_datetime"].dt.dayofweek
    df["time_backet"] = pd.cut(df["pickup_hour"], bin=[-1, 5, 9, 15, 19, 23],
                               labels=["overnight", "Morning", "Midday", "Evening", "Night",]).astype(str)
    df["speed_mph"] = df["trip_distance"] / (df["duratio_min"] / 60)
    df["fare_per_mile"] = df["fare_amount"] / df["trip_distance"]
    df["tip_pct"] = np.where(df["payment_type_id"] == 1, df["tip_amount"] / df["fare_amount"] * 100, np.nan)
    for c in ("pickup_datetime", "dropoff_datetime"):
        df[c] = df[c].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df.round({"duration_min": 2,"speed_mph": 2, "fare_per_mile": 2, "tip_pct": 1})


