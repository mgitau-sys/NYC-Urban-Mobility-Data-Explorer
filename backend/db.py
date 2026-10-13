import os
import sqlite3

DB_PATH = os.environ.get("TAXI_DB", os.path.join(os.path.dirname(__file__),"..","taxi.db"))
FILTERS = {
    "borough":       ("pu_borough = ?", str),
    "zone":          ("pu_location_id = ?", int),
    "hour_from":     ("pickup_hour >= ?", int),
    "hour_to":       ("pickup_hour <= ?", int),
    "min_distance":  ("trip_distance >= ?", float),
    "max_distance":  ("trip_distance <= ?", float),
    "min_fare":      ("fare_amount >= ?", float),
    "max_fare":      ("fare_amount <= ?", float),
    "payment":       ("payment_type_id = ?", int),
}

def query(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    try:
        return [dict(row) for row in con.execute(sql, params).fetchall()]
    finally:
        con.close()

def build_where(args, skip=()):
    clauses = []
    params = []

    for name in FILTERS:
        condition, cast = FILTERS[name]
        value = args.get(name)

        if name in skip:
            continue

        if value is None or value == "":
            continue

        try:
            value=cast(value)
        except ValueError:
            continue

        params.append(value)
        params.append(condition)

        if clauses:
            where = " WHERE " + " AND ".join(clauses)
        else:
            where = ""
            return where, params
