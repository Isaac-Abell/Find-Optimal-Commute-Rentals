import aiohttp
import asyncio
from datetime import datetime, date, time as dtime, timedelta
from config import GOOGLE_API_KEY

async def _fetch_commute_time(session, origin, params):
    """
    Fetch commute time from Distance Matrix API for a single origin-destination pair.
    Returns duration in seconds or None if unavailable.
    """
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            element = data.get("rows", [])[0].get("elements", [])[0]
            if element.get("status") == "OK":
                return element["duration"]["value"]
            return None
    except Exception as e:
        print(f"[ERROR] Failed fetching commute for {origin}: {e}")
        return None


async def compute_commute_times(origins_coords, destination_coord, travel_type="walking"):
    """
    Compute commute durations from multiple origins to a single destination
    using Distance Matrix API.
    Returns a list of durations in seconds (None if unavailable).
    """
    today = date.today()
    arrival_datetime = datetime.combine(today, dtime(hour=9))

    # If it's already past 9:00 AM today, set it to tomorrow 9:00 AM
    if datetime.now() > arrival_datetime:
        arrival_datetime += timedelta(days=1)

    arrival_timestamp = int(arrival_datetime.timestamp())

    async with aiohttp.ClientSession() as session:
        tasks = []
        for origin in origins_coords:
            params = {
                "origins": f"{origin[0]},{origin[1]}",
                "destinations": f"{destination_coord[0]},{destination_coord[1]}",
                "mode": travel_type,
                "key": GOOGLE_API_KEY
            }

            # Required for transit mode
            if travel_type == "transit" or travel_type == "driving":
                params["arrival_time"] = arrival_timestamp

            tasks.append(_fetch_commute_time(session, origin, params))

        results = await asyncio.gather(*tasks)
        return results