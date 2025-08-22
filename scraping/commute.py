from geopy.distance import geodesic
from config import CITY_CENTERS

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