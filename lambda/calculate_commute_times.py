import aiohttp
import asyncio
import datetime
from config import GOOGLE_API_KEY

async def _fetch_transit_time(session, origin, destination, arrival_timestamp):
    """
    Retrieve the estimated transit travel time between a single origin and destination.

    Uses the Google Directions API in 'transit' mode. Each origin requires a separate request
    because the API does not support batching for transit routes.
    
    Args:
        session: An active aiohttp ClientSession.
        origin: Tuple of (latitude, longitude) for the origin point.
        destination: Tuple of (latitude, longitude) for the destination point.
        arrival_timestamp: Desired arrival time as a UNIX timestamp.

    Returns:
        Travel duration in seconds, or None if the request failed or no route was found.
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        "mode": "transit",
        "arrival_time": arrival_timestamp,
        "key": GOOGLE_API_KEY
    }

    try:
        async with session.get(base_url, params=params) as resp:
            data = await resp.json()
            if data.get("status") == "OK":
                return data["routes"][0]["legs"][0]["duration"]["value"]
            return None
    except Exception:
        return None


async def _fetch_transit_times_async(origins_coords, destination_coord, arrival_timestamp):
    """
    Retrieve transit commute times for multiple origins concurrently.

    Since the Directions API does not support multiple origins in one transit request,
    each origin is queried individually using asyncio for concurrency.
    
    Args:
        origins_coords: List of (latitude, longitude) origin coordinates.
        destination_coord: Tuple of (latitude, longitude) for the destination.
        arrival_timestamp: Desired arrival time as a UNIX timestamp.

    Returns:
        List of durations in seconds, one per origin, with None for failed routes.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [
            _fetch_transit_time(session, origin, destination_coord, arrival_timestamp)
            for origin in origins_coords
        ]
        return await asyncio.gather(*tasks)


async def _fetch_batched_times(origins_coords, destination_coord, travel_type, arrival_timestamp):
    """
    Retrieve commute times for multiple origins to a single destination in one batched request.

    Uses the Google Distance Matrix API, which supports multiple origins for driving,
    walking, or bicycling modes. Transit mode is handled separately.

    Args:
        origins_coords: List of (latitude, longitude) origin coordinates.
        destination_coord: Tuple of (latitude, longitude) for the destination.
        travel_type: Travel mode ("driving", "walking", or "bicycling").
        arrival_timestamp: Desired arrival time as a UNIX timestamp.

    Returns:
        List of durations in seconds, one per origin, with None for failed routes.
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    origins_str = "|".join([f"{lat},{lon}" for lat, lon in origins_coords])
    destination_str = f"{destination_coord[0]},{destination_coord[1]}"

    params = {
        "origins": origins_str,
        "destinations": destination_str,
        "mode": travel_type.lower(),
        "arrival_time": arrival_timestamp,
        "key": GOOGLE_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as resp:
            data = await resp.json()
            if data.get("status") == "OK":
                elements = data["rows"]
                return [
                    row["elements"][0]["duration"]["value"]
                    if row["elements"][0].get("status") == "OK" else None
                    for row in elements
                ]
            return [None] * len(origins_coords)


async def compute_commute_times(origins_coords, destination_coord, travel_type="WALK"):
    """
    Compute estimated commute times for multiple origins to a single destination.

    - For driving, walking, or bicycling: Uses the Distance Matrix API in a single batched request.
    - For transit: Uses the Directions API, sending one concurrent request per origin.

    This hybrid approach minimizes API calls when batching is supported while
    leveraging asyncio to speed up modes that require individual requests.

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

    if travel_type.upper() == "TRANSIT":
        return await _fetch_transit_times_async(origins_coords, destination_coord, arrival_timestamp)
    else:
        return await _fetch_batched_times(origins_coords, destination_coord, travel_type, arrival_timestamp)