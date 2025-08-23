from geopy.distance import geodesic
from config import CITY_CENTERS

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