import os
from sqlalchemy import Table, Column, Integer, String, Float, MetaData

metadata = MetaData()

CITY_CENTERS = {
    "San Francisco Bay Area, CA": (37.7749, -122.4194),
    "New York, NY": (40.7128, -74.0060),
    "Seattle, WA": (47.6062, -122.3321),
    "Toronto, ON, Canada": (43.6532, -79.3832),
    "Austin, TX": (30.2672, -97.7431)
}

# --- Google API Key ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Database credentials ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "5432")

listings = Table(
    "listings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("formatted_address", String),
    Column("city", String),
    Column("nearest_city", String),
    Column("list_price", Float),
    Column("beds", Integer),
    Column("full_baths", Integer),
    Column("half_baths", Integer),
    Column("property_url", String),
    Column("latitude", Float),
    Column("longitude", Float)
)