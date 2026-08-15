import duckdb
import random
from datetime import datetime, timedelta

DB_PATH = "/workspace/data/flights.db"

def seed_data(records=200):
    conn = duckdb.connect(DB_PATH)
    
    # Ensure tables exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_logs (
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            airport VARCHAR,
            temperature FLOAT,
            wind_speed FLOAT,
            precipitation FLOAT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS flight_logs (
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            airport VARCHAR,
            plane_count INTEGER
        )
    """)
    
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(records):
        log_time = base_time + timedelta(hours=i * 4)
        
        # Simulate realistic weather
        temp = round(random.uniform(5.0, 35.0), 2)
        wind = round(random.uniform(5.0, 45.0), 2)
        precip = round(random.choice([0.0, 0.0, 0.0, random.uniform(1.0, 15.0)]), 2)
        
        # Simulate flight volume
        plane_count = random.randint(20, 140)
        
        conn.execute(
            "INSERT INTO weather_logs VALUES (?, ?, ?, ?, ?)",
            (log_time, "JFK", temp, wind, precip)
        )
        conn.execute(
            "INSERT INTO flight_logs VALUES (?, ?, ?)",
            (log_time, "JFK", plane_count)
        )
        
    conn.close()
    print(f"Successfully seeded {records} historical records into DuckDB.")

if __name__ == "__main__":
    seed_data()



    