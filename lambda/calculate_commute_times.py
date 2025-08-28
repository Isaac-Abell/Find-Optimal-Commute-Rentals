import aiohttp
import asyncio
import datetime
from config import GOOGLE_API_KEY

async def _fetch_commute_time(session, url, origin, destination, mode_param, arrival_timestamp):
    """
    Retrieves travel time for a single origin-destination pair using a specified URL.
    
    Args:
        session: An active aiohttp ClientSession.
        url: The API endpoint URL to use.
        origin: Tuple of (latitude, longitude) for the origin point.
        destination: Tuple of (latitude, longitude) for the destination point.
        mode_param: The travel mode, correctly cased for the API.
        arrival_timestamp: Desired arrival time as a UNIX timestamp.
        
    Returns:
        Travel duration in seconds, or None if the request failed or no route was found.
    """
    params = {
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        "mode": mode_param,
        "arrival_time": arrival_timestamp,
        "key": GOOGLE_API_KEY
    }
    
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data.get("status") == "OK":
                if "distancematrix" in url:
                    element = data["rows"][0]["elements"][0]
                    if element.get("status") == "OK":
                        return element["duration"]["value"]
                elif "directions" in url:
                    return data["routes"][0]["legs"][0]["duration"]["value"]
            return None
    except Exception:
        return None

async def compute_commute_times(origins_coords, destination_coord, travel_type="WALK"):
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

    directions_url = "https://maps.googleapis.com/maps/api/directions/json"
    distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
    if travel_type.upper() == "TRANSIT":
        url = directions_url
        mode_param = "transit"
    else:
        url = distance_matrix_url
        mode_param = travel_type.upper()
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            _fetch_commute_time(session, url, origin, destination_coord, mode_param, arrival_timestamp)
            for origin in origins_coords
        ]
        return await asyncio.gather(*tasks)