from sqlalchemy import Table, Column, Integer, String, Float, MetaData

metadata = MetaData()

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
    Column("primary_photo", String),
    Column("latitude", Float),
    Column("longitude", Float)
)