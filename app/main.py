import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import schedule
import time
import threading
import duckdb

from app.db.database import init_db, insert_weather, insert_flight
from app.services.weather import fetch_weather
from app.services.opensky import fetch_flight_density
from app.ml.inference import predict_delay

app = FastAPI(title="Flight Disruption Predictor")

JFK_LAT, JFK_LON = 40.6413, -73.7781
JFK_BBOX = {"lamin": 40.0, "lomin": -74.5, "lamax": 41.5, "lomax": -73.0}

# ----------------- INGESTION SCHEDULER -----------------
def ingestion_job():
    weather = fetch_weather(JFK_LAT, JFK_LON)
    insert_weather("JFK", weather["temperature"], weather["wind_speed"], weather["precipitation"])
    
    plane_count = fetch_flight_density(**JFK_BBOX)
    insert_flight("JFK", plane_count)
    print("Ingestion cycle complete.")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.on_event("startup")
def startup_event():
    init_db()
    schedule.every(4).hours.do(ingestion_job)
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

# ----------------- API ENDPOINTS & UI -----------------

# Get absolute path to the static directory to prevent white-screen errors
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount the static directory to serve HTML/JS
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_dashboard():
    """Serves the main frontend UI."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_file)

@app.get("/api/latest-data")
def get_latest_data():
    """Fetches the most recent live telemetry from DuckDB."""
    try:
        conn = duckdb.connect("/workspace/data/flights.db")
        query = """
            SELECT w.temperature, w.wind_speed, w.precipitation, f.plane_count, w.timestamp
            FROM weather_logs w
            JOIN flight_logs f ON w.airport = f.airport 
                AND DATE_TRUNC('hour', w.timestamp) = DATE_TRUNC('hour', f.timestamp)
            ORDER BY w.timestamp DESC LIMIT 1
        """
        result = conn.execute(query).df()
        conn.close()
        
        if result.empty:
            return {"status": "waiting for data"}
        
        record = result.iloc[0]
        return {
            "temperature": float(record['temperature']),
            "wind_speed": float(record['wind_speed']),
            "precipitation": float(record['precipitation']),
            "plane_count": int(record['plane_count']),
            "timestamp": str(record['timestamp'])
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/predict")
def get_prediction():
    """Runs live inference using the latest data."""
    latest = get_latest_data()
    if "error" in latest or "status" in latest:
        return {"error": "Insufficient data for prediction"}
        
    return predict_delay(
        latest["temperature"],
        latest["wind_speed"],
        latest["precipitation"],
        latest["plane_count"]
    )