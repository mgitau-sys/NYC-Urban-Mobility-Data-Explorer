# Urban Mobility Data Explorer

An interactive dashboard that answers one question: **where and when do NYC's yellow cabs slow down, and what does that cost riders per mile?** It cleans one month of NYC TLC yellow-taxi trips, stores them in SQLite, and serves a Leaflet zone map, hourly and busiest-route charts, and a filterable trip table through a Flask API.

- **Live app:** https://nyc-urban-mobility-data-explorer-1.onrender.com/ (free hosting: the first load after a quiet spell can take 30–60 seconds)
- **Video walkthrough:** https://youtu.be/2Jmu44qv78I
- **Technical report (PDF):** [Read the report](https://drive.google.com/file/d/1uCSHyPxFKhuCrSJlbgNMf5avMrLuw4bQ/view?usp=sharing)
- **Team task sheet:** [Brain Boosters task allocation and meeting log](https://docs.google.com/spreadsheets/d/17ZfRFxAy5o7xeZrytVFuyV5gzzx9lc9povi6jo965d8/edit?usp=sharing)

## Team: Brain Boosters

| Member | Role | GitHub | Main contributions |
|---|---|---|---|
| Pauline Moraa | Group leader | [@pmiyenda-dotcom](https://github.com/pmiyenda-dotcom) | Frontend, tests, report and README |
| Marion Gitau | Group member | [@mgitau-sys](https://github.com/mgitau-sys) | Backend, report and README |
| Emmanuel Masambu | Group member | [@EMANU02004](https://github.com/EMANU02004) | ETL pipeline, report and README |

## Project structure

```
etl/        clean.py (cleaning + features), build_database.py, schema.sql
backend/    app.py (Flask API), db.py (filters), algorithms.py (custom min-heap)
frontend/   index.html, app.js, style.css
tests/      test_algorithms.py
```

## Setup

1. Install Python 3.10 or newer, then run:
   ```
   pip install -r requirements.txt
   ```
2. Create two folders in the project root: `data/` and `docs/`.
3. Download these files from the [NYC TLC Trip Record Data page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) and put them in `data/`:
   - one month of Yellow Taxi trips: `yellow_tripdata_[YYYY-MM].parquet`
   - `taxi_zone_lookup.csv`
   - the taxi zones as GeoJSON, saved as `taxi_zones.geojson`, in longitude/latitude (WGS84)

## Build the database

```
python etl/build_database.py --trips data/yellow_tripdata_[YYYY-MM].parquet
```

This creates `taxi.db`, `data/zones_clean.geojson` and `docs/cleaning_report.json`. To keep the database small, add `--max-rows 300000`.

## Run the app locally

```
python backend/app.py
```

Then open http://127.0.0.1:5000.

## Run the tests

```
python tests/test_algorithms.py
```

## Deployment (Render)

| Setting | Value |
|---|---|
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn --chdir backend app:app` |

`taxi.db` and `data/zones_clean.geojson` are committed so the deployed app has data to serve.

## API endpoints

| Endpoint | Returns |
|---|---|
| `/api/summary` | trip count, average fare, distance, speed and tip % |
| `/api/hourly` | trips, speed and fare per mile by pickup hour |
| `/api/zones` | per-zone metrics for the map |
| `/api/trips` | paged, sortable trip list |
| `/api/top-routes?k=10` | busiest routes, ranked by the custom min-heap |
| `/api/exclusions` | rows removed during cleaning, by reason |

All endpoints accept the filters `borough`, `zone`, `hour_from`, `hour_to`, `min_distance`, `max_distance`, `min_fare`, `max_fare` and `payment`.