import pandas as pd
import googlemaps
import json
from sqlalchemy import select, func
from db import engine
from config import MAX_DISTANCE_KM, listings
from commute import nearest_region, compute_commute_times, geodesic_distance
from check_inputs import check_inputs
from config import GOOGLE_API_KEY


def get_listings(user_lat, user_lon, closest_city, filters, sort_by='list_price', ascending=True, page=1, page_size=20):
    """
    Fetch listings from the database with optional filtering, sorting, and distance calculation.

    Distance is computed in SQL only if sorting by distance/commute; otherwise, it is computed in Python
    for the limited page of results to avoid expensive queries.

    Parameters:
        user_lat (float): Latitude of the user location.
        user_lon (float): Longitude of the user location.
        closest_city (str): Region/city to filter listings by proximity.
        filters (dict): Optional filters for price, beds, and baths.
        sort_by (str): Column to sort by. Special values 'distance', 'commute_seconds', 'commute_time'
                       trigger SQL distance computation.
        ascending (bool): Sort order; True for ascending, False for descending.
        page (int): Page number (1-based) for pagination.
        page_size (int): Number of listings per page.

    Returns:
        pd.DataFrame: DataFrame containing the paged listings with 'distance_kilometers' always populated.
    """
    # Determine if we need to sort by distance/commute
    need_distance_sort = sort_by in ['commute_seconds', 'commute_time', 'distance']

    # Base query: no distance computation unless sorting by distance
    query = select(listings).where(listings.c.region == closest_city)

    # Apply optional filters
    if "min_price" in filters:
        query = query.where(listings.c.list_price >= filters["min_price"])
    if "max_price" in filters:
        query = query.where(listings.c.list_price <= filters["max_price"])
    if "min_beds" in filters:
        query = query.where(listings.c.beds >= filters["min_beds"])
    if "max_beds" in filters:
        query = query.where(listings.c.beds <= filters["max_beds"])
    if "min_baths" in filters:
        query = query.where((listings.c.full_baths + listings.c.half_baths / 2) >= filters["min_baths"])
    if "max_baths" in filters:
        query = query.where((listings.c.full_baths + listings.c.half_baths / 2) <= filters["max_baths"])

    # Sorting
    if need_distance_sort:
        # Compute distance in SQL for sorting if necessary
        R = 6371  # Earth radius in kilometers
        distance_expr = R * 2 * func.asin(
            func.sqrt(
                func.pow(func.sin(func.radians(listings.c.latitude - user_lat) / 2), 2) +
                func.cos(func.radians(user_lat)) *
                func.cos(func.radians(listings.c.latitude)) *
                func.pow(func.sin(func.radians(listings.c.longitude - user_lon) / 2), 2)
            )
        ).label('distance_kilometers')
        query = query.add_columns(distance_expr).order_by(distance_expr if ascending else distance_expr.desc())
    else:
        # Sort by other column safely using SQLAlchemy column reference
        if hasattr(listings.c, sort_by):
            col = getattr(listings.c, sort_by)
            query = query.order_by(col.asc() if ascending else col.desc())

    # Pagination
    query = query.limit(page_size).offset((page - 1) * page_size)

    # Execute query
    df = pd.read_sql(query, engine)

    # Compute distance in Python if not sorted by distance
    if 'distance_kilometers' not in df.columns:
        df['distance_kilometers'] = df.apply(
            lambda row: geodesic_distance(user_lat, user_lon, row['latitude'], row['longitude']),
            axis=1
        )

    return df


def lambda_handler(event, context):
    """
    AWS Lambda handler to fetch listings near a user's address, apply filters, 
    compute distances and commute times, and return paginated JSON results.

    Parameters:
        event (dict): Dictionary containing keys:
            - user_address (str): Address to geocode.
            - commute_type (str, optional): Travel mode ('WALK', 'DRIVE', etc.).
            - page (int, optional): Page number for pagination (default 1).
            - page_size (int, optional): Number of listings per page (default 20).
            - filters (dict, optional): Filtering options for price, beds, baths.
            - sort_by (str, optional): Column to sort by (default 'list_price').
            - ascending (bool, optional): Sort order (default True).

    Returns:
        dict: JSON-serializable dictionary containing:
            - page, page_size, total_listings, results (list of dicts)
    """
    try:
        validated = check_inputs(event)
    except ValueError as e:
        print(f"Input validation error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    user_address = validated['user_address']
    commute_type = validated['commute_type']
    page = validated['page']
    page_size = validated['page_size']
    filters = validated['filters']
    sort_by = validated['sort_by']
    ascending = validated['ascending']

    # --- Step 1: Geocode user address ---
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    try:
        geocode_result = gmaps.geocode(user_address)
        user_location = geocode_result[0]['geometry']['location']
        user_lat, user_lon = user_location['lat'], user_location['lng']
    except Exception as e:
        print(f"Failed to geocode address: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Failed to find address: {user_address}"})
        }

    # --- Step 2: Determine nearest city/region ---
    closest_city, min_distance = nearest_region(user_lat, user_lon)

    if min_distance > MAX_DISTANCE_KM:
        print(f"Address is too far from any city center (min distance: {min_distance} km).")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Address is too far from supported city centers."})
        }

    try:
        # --- Step 3: Fetch listings ---
        df = get_listings(user_lat, user_lon, closest_city, filters, sort_by, ascending, page, page_size)
        if df.empty:
            return {"results": [], "total_listings": 0}

        # --- Step 4: Compute commute times for returned listings only ---
        origins_coords = list(zip(df['latitude'], df['longitude']))
        df['commute_seconds'] = compute_commute_times(origins_coords, (user_lat, user_lon), travel_type=commute_type)
        df['commute_minutes'] = df['commute_seconds'] / 60

        # --- Step 5: Prepare JSON response ---
        columns = ['formatted_address', 'city', 'region', 'list_price', 'beds',
                'full_baths', 'half_baths', 'property_url', 'latitude', 'longitude',
                'distance_kilometers', 'commute_minutes', 'primary_photo']
        results = df[columns].to_dict(orient="records")

    except Exception as e:
        print(f"Error processing listings: {e}")

        if "Transit route not found" in str(e):
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "Transit route not found"})
                }

        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Failed to process listings"})
        }

    return {
        "page": page,
        "page_size": page_size,
        "total_listings": len(df),
        "results": results
    }