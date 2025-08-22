import os
from sqlalchemy import Table, Column, Integer, String, Float, MetaData

metadata = MetaData()

CITY_CENTERS = {
    "San Francisco Bay Area, CA": (37.7749, -122.4194),
    "New York, NY": (40.7128, -74.0060),
    "Seattle, WA": (47.6062, -122.3321),
    "Austin, TX": (30.2672, -97.7431),
    "Boston, MA": (42.3601, -71.0589),
    "Denver, CO": (39.7392, -104.9903),
    "Los Angeles, CA": (34.0522, -118.2437)
}

MAX_DISTANCE_MILES = 50

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
DB_USER = os.environ.get("username")
DB_PASSWORD = os.environ.get("password")
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT", "5432")

# --- SQLAlchemy table definition ---
listings = Table(
    "listings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("formatted_address", String),
    Column("city", String),
    Column("region", String),
    Column("list_price", Float),
    Column("beds", Integer),
    Column("full_baths", Integer),
    Column("half_baths", Integer),
    Column("property_url", String),
    Column("latitude", Float),
    Column("longitude", Float)
)
