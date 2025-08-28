import requests
import json
import datetime
from geopy.distance import geodesic
from config import CITY_CENTERS, GOOGLE_API_KEY

def nearest_region(lat, lon):
    """Finds the closest city center to a given latitude and longitude, and distance in kilometers."""
    closest = None
    min_distance_km = float('inf')
    for city, (city_lat, city_lon) in CITY_CENTERS.items():
        distance_km = geodesic((lat, lon), (city_lat, city_lon)).km
        if distance_km < min_distance_km:
            min_distance_km = distance_km
            closest = city
    return closest, min_distance_km

def geodesic_distance(lat1, lon1, lat2, lon2):
    """Compute the geodesic distance between two points (in kilometers)."""
    return geodesic((lat1, lon1), (lat2, lon2)).km

def compute_commute_times(origins_coords, destination_coord, travel_type="WALK"):
    """Compute commute times for multiple origins to one destination using Google APIs."""

    today = datetime.date.today()
    arrival_time_str = f"{today.year}-{today.month}-{today.day} 09:00:00"
    arrival_datetime = datetime.datetime.strptime(arrival_time_str, "%Y-%m-%d %H:%M:%S")
    arrival_timestamp = int(arrival_datetime.timestamp())

    results = []

    # --- TRANSIT: legacy Directions API ---
    if travel_type == "TRANSIT":
        base_url = "https://maps.googleapis.com/maps/api/directions/json"
        
        for lat, lon in origins_coords:
            params = {
                "origin": f"{lat},{lon}",
                "destination": f"{destination_coord[0]},{destination_coord[1]}",
                "mode": "transit",
                "arrival_time": arrival_timestamp,
                "key": GOOGLE_API_KEY
            }
            
            try:
                r = requests.get(base_url, params=params)
                r.raise_for_status()
                data = r.json()
                if data.get("status") == "OK":
                    duration_seconds = data["routes"][0]["legs"][0]["duration"]["value"]
                    results.append(duration_seconds)
                else:
                    results.append(None)
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

    for lat, lon in origins_coords:
        payload = {
            "origin": {"location": {"latLng": {"latitude": lat, "longitude": lon}}},
            "destination": {"location": {"latLng": {
                "latitude": destination_coord[0],
                "longitude": destination_coord[1]
            }}},
            "travelMode": travel_type,
            "arrival_time": arrival_timestamp
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