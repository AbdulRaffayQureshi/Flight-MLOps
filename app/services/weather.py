# External API Connectors
# The Open-Meteo API accepts a geographic coordinate (latitude and longitude) to provide 
# localized weather data, including variables like temperature and wind speed (windspeed_10m)

import requests
def fetch_weather(lat: float, lon: float) -> dict:
    """"Fetches the live weather data from Open-Meteo API"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation"

    try:
        response = requests.get(url)
        response.raise_for_status()
        current = response.json().get("current", {})

        return{
            "temperature": current.get("temperature_2m", 0.0),
            "wind_speed": current.get("wind_speed_10m", 0.0),
            "precipitation": current.get("precipitation", 0.0)
        }
    except Exception as e:
        print(f"Weather API Error: {e}")
        return{"temperature": 0.0, "wind_speed": 0.0, "precipitation": 0.0}
    