import googlemaps
import json
import asyncio
from config import MAX_DISTANCE_KM
from db import get_listings
from calculate_distance import nearest_region
from calculate_commute_times import compute_commute_times
from check_inputs import check_inputs
from config import GOOGLE_API_KEY

def lambda_handler(event, context):
    """
    AWS Lambda handler to fetch listings near a user's address, apply filters, 
    compute distances and commute times, and return paginated JSON results.

    Parameters:
    event (dict): Dictionary containing keys:
        - user_address (str): Address to geocode.
        - commute_type (str, optional): Travel mode ('walking', 'driving', etc.).
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
        
        commute_times = asyncio.run(compute_commute_times(origins_coords, (user_lat, user_lon), travel_type=commute_type))

        df['commute_seconds'] = commute_times
        df['commute_minutes'] = df['commute_seconds'] / 60

        df.dropna(subset=['commute_seconds'], inplace=True)

        df['commute_url'] = df.apply(
            lambda row: (
                f"https://www.google.com/maps/dir/?api=1"
                f"&origin={row['latitude']},{row['longitude']}"
                f"&destination={user_lat},{user_lon}"
                f"&travelmode={commute_type.lower()}"
            ),
            axis=1
        )

        if df.empty:
            raise ValueError("Transit routes not found.")

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
            "body": json.dumps({"error": "Failed to process listings"})
        }

    return {
        "page": page,
        "page_size": page_size,
        "total_listings": len(df),
        "results": results
    }