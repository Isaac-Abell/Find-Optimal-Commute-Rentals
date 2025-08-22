import json
import boto3
from sqlalchemy import Table, Column, Integer, String, Float, MetaData

metadata = MetaData()

CITY_CENTERS = {
    "San Francisco Bay Area, CA": (37.7749, -122.4194),
    "New York, NY": (40.7128, -74.0060),
    "Seattle, WA": (47.6062, -122.3321),
    "Toronto, ON, Canada": (43.6532, -79.3832),
    "Austin, TX": (30.2672, -97.7431)
}

# --- Fetch secrets from AWS Secrets Manager ---
def get_secrets(secret_name="commute-secrets", region_name="us-east-1"):
    """
    Retrieves secrets from AWS Secrets Manager.
    Assumes the secret is stored as a JSON object with keys:
    GOOGLE_API_KEY, DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_PORT
    """
    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret_dict = json.loads(response["SecretString"])
    return secret_dict

# Cache secrets so we only fetch them once per cold start
_secrets = get_secrets()

GOOGLE_API_KEY = _secrets.get("GOOGLE_API_KEY")
DB_USER = _secrets.get("DB_USER")
DB_PASSWORD = _secrets.get("DB_PASSWORD")
DB_HOST = _secrets.get("DB_HOST")
DB_NAME = _secrets.get("DB_NAME")
DB_PORT = _secrets.get("DB_PORT", "5432")

# --- SQLAlchemy table definition ---
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