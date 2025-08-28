"""
geocoding.py
------------
Handles geocoding of user addresses and validation against supported regions.
"""

import googlemaps
from config import MAX_DISTANCE_KM, GOOGLE_API_KEY
from calculate_distance import nearest_region


def geocode_user_address(address: str) -> tuple[float, float]:
    """
    Convert a user-provided address to latitude and longitude.

    Args:
        address (str): The address to geocode.

    Returns:
        (float, float): Latitude and longitude.

    Raises:
        ValueError: If the address cannot be geocoded.
    """
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    try:
        geocode_result = gmaps.geocode(address)
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    except Exception:
        raise ValueError(f"Failed to find address: {address}")


def validate_city(lat: float, lon: float) -> str:
    """
    Determine the nearest supported city for a given location.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.

    Returns:
        str: Name of the nearest city.

    Raises:
        ValueError: If no nearby city is within MAX_DISTANCE_KM.
    """
    city, min_distance = nearest_region(lat, lon)
    if min_distance > MAX_DISTANCE_KM:
        raise ValueError("Address is too far from supported city centers.")
    return city
