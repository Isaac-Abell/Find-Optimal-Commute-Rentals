import aiohttp
import asyncio
import datetime
from config import GOOGLE_API_KEY


async def _fetch_commute_time(session, origin, destination, url, params):
    """
    Retrieves travel time for a single origin-destination pair using a specified API endpoint.

    This function supports both the Google Directions API (for transit) and the
    Distance Matrix API (for driving, walking, or bicycling). It handles errors
    gracefully and returns None if the request fails or no route is found.

    Args:
        session: An active aiohttp ClientSession.
        origin: Tuple of (latitude, longitude) for the origin point.
        destination: Tuple of (latitude, longitude) for the destination point.
        url: The API endpoint URL to use.
        params: Dictionary of query parameters to send with the request, 
                including API key, mode, and arrival_time.

    Returns:
        int or None: Travel duration in seconds if available, or None if no valid route is found.
    """
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data.get("status") == "OK":
                if "routes" in data:  # Transit (Directions API)
                    return data["routes"][0]["legs"][0]["duration"]["value"]
                elif "rows" in data:  # Driving/walking/bicycling (Distance Matrix API)
                    element = data["rows"][0]["elements"][0]
                    if element.get("status") == "OK":
                        return element["duration"]["value"]
            return None
    except Exception as e:
        print(f"[ERROR] Failed fetching commute for {origin}: {e}")
        return None


async def compute_commute_times(origins_coords, destination_coord, travel_type="WALKING"):
    """
    Compute estimated commute times for multiple origins using concurrent requests for each origin.

    Args:
        origins_coords: List of (latitude, longitude) origin coordinates.
        destination_coord: Tuple of (latitude, longitude) for the destination.
        travel_type: Travel mode. One of "DRIVING", "WALKING", "BICYCLING", or "TRANSIT".

    Returns:
        List of commute durations in seconds, one per origin, or None for any failed/invalid routes.
    """
    today = datetime.date.today()
    arrival_time_str = f"{today.year}-{today.month}-{today.day} 09:00:00"
    arrival_datetime = datetime.datetime.strptime(arrival_time_str, "%Y-%m-%d %H:%M:%S")
    arrival_timestamp = int(arrival_datetime.timestamp())

    async with aiohttp.ClientSession() as session:
        tasks = []
        for origin in origins_coords:
            if travel_type.upper() == "TRANSIT":
                url = "https://maps.googleapis.com/maps/api/directions/json"
                params = {
                    "origin": f"{origin[0]},{origin[1]}",
                    "destination": f"{destination_coord[0]},{destination_coord[1]}",
                    "mode": "transit",
                    "arrival_time": arrival_timestamp,
                    "key": GOOGLE_API_KEY
                }
            else:
                url = "https://maps.googleapis.com/maps/api/distancematrix/json"
                params = {
                    "origins": f"{origin[0]},{origin[1]}",
                    "destinations": f"{destination_coord[0]},{destination_coord[1]}",
                    "mode": travel_type.lower(),
                    "arrival_time": arrival_timestamp,
                    "key": GOOGLE_API_KEY
                }

            tasks.append(_fetch_commute_time(session, origin, destination_coord, url, params))

        results = await asyncio.gather(*tasks)
        return results