import requests
import json
from geopy.distance import geodesic
from config import CITY_CENTERS, GOOGLE_API_KEY

def nearest_region(lat, lon):
    """Finds the closest city center to a given latitude and longitude, and distance in miles."""
    closest = None
    min_distance = float('inf')
    for city, (city_lat, city_lon) in CITY_CENTERS.items():
        distance = geodesic((lat, lon), (city_lat, city_lon)).miles
        if distance < min_distance:
            min_distance = distance
            closest = city
    return closest, min_distance

def compute_commute_times(origins_coords, destination_coord, travel_type="WALK"):
    """Compute commute times for multiple origins to one destination using Google APIs."""
    
    # --- TRANSIT: legacy Directions API ---
    if travel_type == "TRANSIT":
        base_url = "https://maps.googleapis.com/maps/api/directions/json"
        results = []
        for lat, lon in origins_coords:
            params = {
                "origin": f"{lat},{lon}",
                "destination": f"{destination_coord[0]},{destination_coord[1]}",
                "mode": "TRANSIT",
                "departure_time": "now",
                "key": GOOGLE_API_KEY
            }
            try:
                r = requests.get(base_url, params=params)
                r.raise_for_status()
                data = r.json()
                if data.get("status") != "OK":
                    results.append(None)
                    continue
                duration_seconds = data["routes"][0]["legs"][0]["duration"]["value"]
                results.append(duration_seconds)
            except Exception:
                results.append(None)
        return results

    # --- Other travel modes: Routes API ---
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "routes.duration"
    }

    results = []
    for lat, lon in origins_coords:
        payload = {
            "origin": {"location": {"latLng": {"latitude": lat, "longitude": lon}}},
            "destination": {"location": {"latLng": {
                "latitude": destination_coord[0],
                "longitude": destination_coord[1]
            }}},
            "travelMode": travel_type
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()
            duration_str = data["routes"][0]["duration"]
            results.append(int(duration_str.replace('s', '')))
        except Exception:
            results.append(None)
    return results
