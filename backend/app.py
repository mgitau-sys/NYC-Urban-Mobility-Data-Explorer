import os
from flask import Flask, jsonify, request, send_from_directory
from algorithms import top_k
from db import build_where, query

Root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
app = Flask(__name__, static_folder=os.path.join(Root, "frontend"), static_url_path="")

SORTABLE = {"pickup_datetime", "pu_zone", "do_zone", "trip_distance", "duration_min", "speed_mph",
            "fare_amount", "tip_pct", "payment_type"}
TRIP_COLUMNS = "pickup_datetime", "pu_zone", "do_zone", "trip_distance", "duration_min", "speed_mph", "fare_amount", "tip_pct", "payment_type"

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/geojson")
def geojson():
    return send_from_directory (os.path.join(Root, "data"), "zones_clean.geojson")

@app.route("/api/summary")
def summary():
    where, params = build_where(request.args)
    sql = ("SELECT COUNT(*) AS trips, AVG(fare_amount) AS avg_fare, AVG(trip_distance) AS avg_distance, "
           "AVG(speed_mph) AS avg_speed, AVG(tip_pct) AS avg_tip_pct FROM trip_view" + where)
    return jsonify(query(sql, params)[0])

@app.route("/api/hourly")
def hourly():
    where, params = build_where(request.args)
    sql = ("SELECT pickup_hour AS hour, COUNT(*) AS trips, AVG(speed_mph) AS avg_speed,"
           "AVG(fare_per_mile) AS avg_fare_per_mile FROM trip_view" + where + 
           " GROUP BY pickup_hour ORDER BY pickup_hour")
    return jsonify(query(sql, params))

@app.rout("/api/zones")
def zones():
    where, params = build_where(request.args, skip=("zone",))
    sql = ("SELECT pu_location_id AS location_id, pu_zone AS zone, COUNT(*) AS trips, AVG(fare_per_mile) AS avg_fare_per_mile,"
           "AVG(speed_mph) AS avg_speed, AVG(tip_pct) AS avg_tip_pct FROM trip_view" + where +
           "GROUP BY pu_location_id")
    return jsonify(query(sql, params))

@app.route("/api/trips")
def  trips():
    where, params = build_where(request.args)

    sort = request.args.get("sort", "pickup_datetime")
    if sort not in SORTABLE:
        sort = "pickup_datetime"
    order = request.args.get("order")
    if order == "asc":
        direction = "ASC"
    else:
        direction = "DESC"

    size = min(request.args.get("size", 15, type=int), 100)
    page = max(request.args.get("page", 1, type=int), 1)
    sql = (f"SELECT {TRIP_COLUMNS} FROM trip_view{where} ORDER BY {sort} {direction} LIMIT ? OFFSET")

    return jsonify(query(sql, params + [size, (page -1) * size]))

@app.route("/api/top-routes")
def top_routes():
    k = min(max(request.args.get("k", 10, type=int), 1), 50)
    where, params = build_where(request.args, skip=("zone",))
    routes = query("SELECT pu_location_id, pu_zone, do_location_id, do_zone, COUNT(*) AS trips, "
                   "AVG(fare_amount) AS avg_fare FROM trip_view" + where +
                   " GROUP BY pu_location_id, do_location_id", params)
    best = top_k(routes, k, lambda r: r["trips"])
    centroids = {z["location_id"]: z for z in query("SELECT location_id, centroid_lat, centroid_lon FROM zones")}
    for r in best:
        a, b = centroids.get(r["pu_location_id"], {}), centroids.get(r["do_location_id"], {})
        r["from"] = [a.get("centroid_lat"), a.get("centroid_lon")]
        r["to"] = [b.get("centroid_lat"), b.get("centroid_lon")]
    return jsonify(best)

@app.route("/api/exclusions")
def exclusions():
    return jsonify(query("SELECT reason, COUNT(*) AS rows FROM excluded_records GROUP BY reason ORDER BY rows DESC"))

if __name__ == "__main__":
    app.run(debug=True)
    