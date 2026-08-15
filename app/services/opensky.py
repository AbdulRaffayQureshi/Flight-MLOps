# he OpenSky Network API allows us to define a geographic bounding box using lamin (latitude minimum), 
# lomin (longitude minimum), lamax, and lomax to count every aircraft currently in that airspace.

import requests

def fetch_flight_density(lamin: float, lomin: float, lamax: float, lomax: float) -> int:
    """Fetches the total number of aircraft currently in the specified bounding box."""
    url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"


    try:
    # 🧐 Note: OpenSky limits anonymous API calls, but it's sufficient for a 4-hour interval.
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        states = response.json().get("states")

        # 🧐 Note: OpenSky limits anonymous API calls, but it's sufficient for a 4-hour interval.
        if states:
            return len(states)
        return 0
    except Exception as e:
        print(f"OpenSky API Error: {e}")
        return 0