print("importing")
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from homeharvest import scrape_property
from geopy.distance import geodesic
from commute import nearest_region
from db import engine
from config import CITY_CENTERS

# Maximum distance (miles) from a tech city to include a listing
MAX_DISTANCE_MILES = 50

def lambda_handler(event, context):
    """
    AWS Lambda function to scrape rental listings weekly
    and replace the listings table in PostgreSQL.
    """
    all_properties = []

    for city in CITY_CENTERS.keys():
        print(f"Scraping listings for {city}...")
        try:
            df = scrape_property(
                location=city,
                listing_type="for_rent",
                past_days=7  # scrape past week
            )

            if df.empty:
                print(f"No listings returned for {city}")
                continue

            # Drop rows with invalid coordinates
            df = df.dropna(subset=["latitude", "longitude"])
            if df.empty:
                print(f"No valid coordinates for {city}")
                continue

            # Determine nearest tech region and distance
            df['region'], df['distance_to_city'] = zip(*df.apply(
                lambda row: nearest_region(row['latitude'], row['longitude']),
                axis=1
            ))

            # Filter listings by MAX_DISTANCE_MILES
            df = df[df['distance_to_city'] <= MAX_DISTANCE_MILES]
            if df.empty:
                print(f"No listings within {MAX_DISTANCE_MILES} miles for {city}")
                continue

            df['last_updated'] = datetime.utcnow()
            all_properties.append(df)
            print(f"Scraped {len(df)} listings for {city}")

        except Exception as e:
            print(f"Failed to scrape {city}: {e}")

    if not all_properties:
        print("No data scraped. Aborting update.")
        return {"statusCode": 500, "body": "No data scraped"}

    combined_df = pd.concat(all_properties, ignore_index=True)

    # Define the columns to keep for the final table
    desired_columns = [
        'property_url',
        'latitude',
        'longitude',
        'beds',
        'full_baths',
        'half_baths',
        'list_price',
        'formatted_address',
        'city',
        'region'
    ]

    # Filter the DataFrame to include only the desired columns
    # We use .get() to avoid KeyErrors if a column is missing from the scraped data
    filtered_df = combined_df[
        [col for col in desired_columns if col in combined_df.columns]
    ]
    filtered_df.loc['id'] = range(1, len(filtered_df) + 1)

    print("adding tables to database")
    with engine.begin() as conn:

        filtered_df.to_sql(
            'listings',        # table name
            conn,
            schema='public',   # explicitly set schema
            if_exists='replace',
            index=False
        )

        # Add primary key constraint safely
        try:
            conn.execute(text("""
                ALTER TABLE public.listings
                ADD PRIMARY KEY (id);
            """))
        except Exception:
            # Might fail if primary key already exists or duplicates exist; ignore
            pass

    print(f"Database replaced with {len(filtered_df)} rental listings.")