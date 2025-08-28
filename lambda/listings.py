"""
listings.py
-----------
Fetches property listings, computes commute times, and formats the results for output.
"""

import asyncio
from utils.time_utils import default_arrival_timestamp
from db import get_listings
from calculate_commute_times import compute_commute_times


def get_listings_with_commute(user_coords, closest_city, filters, sort_by, ascending,
                              page, page_size, commute_type):
    """
    Fetch listings, compute commute times, and return formatted data.

    Args:
        user_coords (tuple): (latitude, longitude) of the user.
        closest_city (str): Closest supported city.
        filters (dict): Filter parameters for listings.
        sort_by (str): Column to sort by.
        ascending (bool): Sort order.
        page (int): Current page.
        page_size (int): Listings per page.
        commute_type (str): Travel mode ('DRIVING', 'TRANSIT', 'WALKING', etc.).

    Returns:
        (list, int): Formatted listing data and total listing count.
    """
    df = get_listings(user_coords[0], user_coords[1], closest_city,
                      filters, sort_by, ascending, page, page_size)

    if df.empty:
        return [], 0

    df = add_commute_data(df, user_coords, commute_type)
    results = format_listings(df, user_coords, commute_type)

    return results, len(df)


def add_commute_data(df, user_coords, travel_type: str):
    """
    Add commute times to a DataFrame of listings.

    Args:
        df (DataFrame): Listings data.
        user_coords (tuple): (latitude, longitude) of the user.
        travel_type (str): Travel mode.

    Returns:
        DataFrame: Updated with commute times.
    """
    origins_coords = list(zip(df['latitude'], df['longitude']))
    commute_times = asyncio.run(compute_commute_times(origins_coords, user_coords, travel_type=travel_type))

    df['commute_seconds'] = commute_times
    df.dropna(subset=['commute_seconds'], inplace=True)
    df['commute_minutes'] = df['commute_seconds'] / 60
    return df


def format_listings(df, user_coords, commute_type: str):
    """
    Format listings with commute URLs and selected columns.

    Args:
        df (DataFrame): Listings data.
        user_coords (tuple): (latitude, longitude) of the user.
        commute_type (str): Travel mode.

    Returns:
        list: List of dictionaries for JSON output.
    """
    arrival_param = get_arrival_time_param(commute_type)
    user_lat, user_lon = user_coords

    df['commute_url'] = df.apply(
        lambda row: (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={row['latitude']},{row['longitude']}"
            f"&destination={user_lat},{user_lon}"
            f"&travelmode={commute_type.lower()}"
            f"{arrival_param}"
        ),
        axis=1
    )

    columns = [
        'formatted_address', 'city', 'region', 'list_price', 'beds',
        'full_baths', 'half_baths', 'property_url', 'latitude', 'longitude',
        'distance_kilometers', 'commute_minutes', 'primary_photo', 'commute_url'
    ]
    return df[columns].to_dict(orient="records")


def get_arrival_time_param(commute_type: str) -> str:
    """
    Generate a Google Maps arrival_time parameter if applicable.

    Args:
        commute_type (str): Travel mode.

    Returns:
        str: Query string for arrival_time.
    """
    if commute_type.upper() not in ["DRIVING", "TRANSIT"]:
        return ""
    arrival_param = f"&arrival_time={default_arrival_timestamp()}" if commute_type.upper() in ["DRIVING","TRANSIT"] else ""
    return arrival_param