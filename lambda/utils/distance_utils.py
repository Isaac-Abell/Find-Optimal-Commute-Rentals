from geopy.distance import geodesic
from config.constants import CITY_CENTERS

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