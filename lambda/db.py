import pandas as pd
from sqlalchemy import create_engine, select, func
from config import listings
from calculate_distance import geodesic_distance

from config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_PORT

db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

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