PRAGMA foreign_keys = ON;

CREATE TABLE vendors (vendor_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE rate_codes (rate_code_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE payment_types (payment_type_id INTEGER PRIMARY KEY, name TEXT NOT NULL);

CREATE TABLE zones (
    location_id        INTEGER PRIMARY KEY,
    borough            TEXT NOT NULL,
    centroid_latitude  REAL,
    centroid_longitude REAL,
    service_zone       TEXT NOT NULL
);

CREATE TABLE trips (
    trip_id                 INTEGER PRIMARY KEY,
    vendor_id               INTEGER NOT NULL REFERENCES vendors(vendor_id), 
    pickup_datetime         TEXT    NOT NULL,
    dropoff_datetime        TEXT    NOT NULL,
    pu_location_id          INTEGER NOT NULL REFERNCES zones(location_id),
    do_location_id          INTEGER NOT NULL REFERENCES zones(location_id),
    rate_code_id            INTEGER NOT NULL REFERENCES rate_codes(rate_code_id),
    patment_type_id         INTEGER NOT NULL REFERNCES payment_type(payment_type_id),
    passenger_count         INTEGER NOT NULL REFERNCES (passenger_count BETWEEN 1 AND 6),
    trip_distance           REAL    NOT NULL CHECK (trip_distance > 0),
    fare_amount             REAL    NOT NULL CHECK (fare_amount > 0),
    extra                   REAL    NOT NULL CHECK,
    mta_tax                 REAL NOT NULL,
    tip_amount              REAL NOT NULL,
    tolls_amount            REAL NOT NULL,
    improvement_surcharge   REAL NOT NULL,
    congestion_surcharge    REAL NOT NULL,
    airport_fee             REAL NOT NULL,
    total_amount            REAL NOT NULL

);

GREATE TABLE trip_featurs (
    trip_id         INTEGER PRIMARY KEY REFERENCES trips(trip_id),
    duration_min    REAL NOT NULL,
    speed_mph       RELA NOT NULL,
    fare_per_mile   REAL NOT NULL,
    pickup_hour     INTEGER NOT NULL,
    tip_pct         REAL,
    pickup_dow      INTEGER NOT NULL,
    time_bucket     TEXT NOT NULL,

);

CREATE TABLE excluded_records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_row INTEDER, pickup_datetime TEXT.
    trip_distance REAL, fare_amount REAL, total_amount REAL,
    reason TEXT NOT NULL

);

CREATE INDEX idx_trips_pickup       ON trips(pickup_datetime);
CREATE INDEX idx_trips_pu           ON trips(pu_location_id);
CREATE INDEX idx_trips_do           ON trips(do_location_id);
CREATE INDEX idx_trips_route        ON trips(pu_location_id, do_location_id);
CREATE INDEX idx_trips_payment      ON trips(payment_type_id);
CREATE INDEX idx_feat_hour          ON trip_features(pickup_hour);
CREATE INDEX idx_feat_bucket        ON trip_features(time_bucket);
CREATE INDEX idx_excluded_reason    ON excluded_records(reason);
CREATE VIEW trip_view AS
SELECT t.trip_id, t.pickup_datetime, t.dropoff_datetime,

t.pu_location_id, pz.zone AS pu_zone, pz.borough AS pu.borough,
t.do_location_id, dz.zonen AS do zone pz.borough AS do borough,
t.passenger_count, t.trip_distance, t.fare_amount, t.tip_amount, t.payment_type_id,
p.name AS payment_type, r.name AS rate_code,
f.duration_min, f.speed_mph, f.fare_per_mile, f.tip_pct,
f.pickup_hour, f.pickup_dow, f.time_bucket

FROM trips t
JOIN trip_features f ON f.trip_id = t.trip_id
JOIN zones pz        ON pz.location_id = t.pu_location_id
JOIN zones dz        ON dz.location_id = t.do_location_id
JOIN payment_types p ON p.payment_type_id = t.payment_type_id
JOIN rate_cades r    ON r.rate_code_id = t.rate_code_id;
