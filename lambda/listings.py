import pandas as pd
import googlemaps
from sqlalchemy import select
from db import engine
from config import listings
from commute import nearest_region, compute_commute_times
from config import GOOGLE_API_KEY

def lambda_handler(event, context):
    """Fetch listings near a user's address and rank them by commute time (after paging)."""
    user_address = event['user_address']
    commute_type = event.get('commute_type', 'WALK')
    page = event.get('page', 1)
    page_size = event.get('page_size', 20)
    filters = event.get('filters', {})
    sort_by = event.get('sort_by', ['list_price'])  # now sorting defaults to price
    ascending = event.get('ascending', [True] * len(sort_by))

    # --- Step 1: Geocode ---
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    try:
        geocode_result = gmaps.geocode(user_address)
        user_location = geocode_result[0]['geometry']['location']
        user_lat, user_lon = user_location['lat'], user_location['lng']
    except Exception as e:
        print(f"Failed to geocode address: {e}")
        return pd.DataFrame()

    # --- Step 2: Nearest city ---
    closest_city, _ = nearest_region(user_lat, user_lon)

    # --- Step 3: Query database with filters ---
    query = select(listings).where(listings.c.region == closest_city)
    if "min_price" in filters:
        query = query.where(listings.c.list_price >= filters["min_price"])
    if "max_price" in filters:
        query = query.where(listings.c.list_price <= filters["max_price"])
    if "min_beds" in filters:
        query = query.where(listings.c.beds >= filters["min_beds"])
    if "max_beds" in filters:
        query = query.where(listings.c.beds <= filters["max_beds"])
    if "min_baths" in filters:
        query = query.where((listings.c.full_baths + listings.c.half_baths/2) >= filters["min_baths"])
    if "max_baths" in filters:
        query = query.where((listings.c.full_baths + listings.c.half_baths/2) <= filters["max_baths"])

    df = pd.read_sql(query, engine)
    if df.empty:
        return pd.DataFrame()

    # --- Step 4: Sort by non-commute columns ---
    for col, asc_flag in reversed(list(zip(sort_by, ascending))):
        if col in df.columns:
            df = df.sort_values(col, ascending=asc_flag, kind='mergesort')

    # --- Step 5: Pagination (before commute computation) ---
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    df_page = df.iloc[start_idx:end_idx]

    # --- Step 6: Compute commute times only for this subset ---
    origins_coords = list(zip(df_page['latitude'], df_page['longitude']))
    df_page['commute_seconds'] = compute_commute_times(
        origins_coords, (user_lat, user_lon), travel_type=commute_type
    )
    df_page = df_page[df_page['commute_seconds'].notnull()]
    df_page['commute_minutes'] = df_page['commute_seconds'] / 60

    # --- Step 7: Return subset with commute info ---
    columns = ['formatted_address', 'city', 'region', 'list_price', 'beds',
               'full_baths', 'half_baths', 'property_url', 'commute_minutes',
               'latitude', 'longitude']
    return df_page[columns].to_dict(orient="records")