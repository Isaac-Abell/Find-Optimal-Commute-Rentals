import pandas as pd
import googlemaps
from sqlalchemy import select
from db import engine
from config import listings
from commute import nearest_region, compute_commute_times

def lambda_handler(user_address, commute_type="WALK", page=1, page_size=20,
                      filters=None, sort_by=None, ascending=None):
    """Fetch listings near a user's address and rank them by commute time."""
    filters = filters or {}
    sort_by = sort_by or ["commute_minutes"]
    ascending = ascending or [True] * len(sort_by)

    # --- Step 1: Geocode ---
    gmaps = googlemaps.Client(key=None)  # Will automatically pick up env var
    try:
        geocode_result = gmaps.geocode(user_address)
        user_location = geocode_result[0]['geometry']['location']
        user_lat, user_lon = user_location['lat'], user_location['lng']
    except Exception as e:
        print(f"Failed to geocode address: {e}")
        return pd.DataFrame()

    # --- Step 2: Nearest city ---
    closest_city, _ = nearest_region(user_lat, user_lon)

    # --- Step 3: Query database ---
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

    # --- Step 4: Compute commute ---
    origins_coords = list(zip(df['latitude'], df['longitude']))
    df['commute_seconds'] = compute_commute_times(origins_coords, (user_lat, user_lon), travel_type=commute_type)
    df = df[df['commute_seconds'].notnull()]
    df['commute_minutes'] = df['commute_seconds'] / 60

    # --- Step 5: Sorting ---
    for col, asc_flag in reversed(list(zip(sort_by, ascending))):
        if col in df.columns:
            df = df.sort_values(col, ascending=asc_flag, kind='mergesort')

    # --- Step 6: Pagination ---
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    df_page = df.iloc[start_idx:end_idx]

    columns = ['formatted_address', 'city', 'region', 'list_price', 'beds',
               'full_baths', 'half_baths', 'property_url', 'commute_minutes',
               'latitude', 'longitude']
    return df_page[columns]