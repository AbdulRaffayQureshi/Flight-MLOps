# DuckDB is a high-performance database that runs entirely out of a single file. 
# We will configure it to store the logs for both the weather conditions and the volume of air traffic.


import duckdb
import os

DB_PATH = "/workspace/data/flights.db"

def init_db():
    """Create the necessary tables if they don't already exist."""
    conn = duckdb.connect(DB_PATH)

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
    conn.close()

def insert_weather(airport, temp, wind, precip):
    conn = duckdb.connect(DB_PATH)
    conn.execute(
        "INSERT INTO weather_logs (airport, temperature, wind_speed, precipitation) VALUES (?, ?, ?, ?)", 
        (airport, temp, wind, precip)
    )
    conn.close()

def insert_flight(airport, count):
    conn = duckdb.connect(DB_PATH)
    conn.execute(
        "INSERT INTO flight_logs (airport, plane_count) VALUES (?, ?)", 
        (airport, count)
    )
    conn.close()