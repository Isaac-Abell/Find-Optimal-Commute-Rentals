import pandas as pd
import boto3
from datetime import datetime
from io import StringIO
from homeharvest import scrape_property
from .commute import nearest_region
from config.constants import CITY_CENTERS, MAX_DISTANCE_KM

def scrape_and_save_to_s3(s3_bucket, s3_key, region_name="us-east-1"):
    """
    Scrapes rental listings, processes the data, and saves it as a CSV file to S3.
    
    Args:
        s3_bucket (str): The name of the S3 bucket.
        s3_key (str): The object key (path and filename) for the CSV in S3.
        region_name (str): The AWS region for the S3 bucket.
        
    Returns:
        bool: True if data was successfully scraped and saved, False otherwise.
    """
    all_properties = []
    s3_client = boto3.client('s3', region_name=region_name)

    for city in CITY_CENTERS.keys():
        print(f"Scraping listings for {city}...")
        try:
            df = scrape_property(
                location=city,
                listing_type="for_rent",
                past_days=30
            )
            
            if df.empty:
                print(f"No listings returned for {city}")
                continue

            # Remove rows missing latitude or longitude
            df = df.dropna(subset=["latitude", "longitude"])
            if df.empty:
                print(f"No valid coordinates for {city}")
                continue

            # Fill NaNs for full_baths and half_baths with 0
            # Fill NaNs for full_baths and half_baths with 0 and ensure numeric type
            if 'full_baths' in df.columns:
                df['full_baths'] = pd.to_numeric(df['full_baths'], errors='coerce').fillna(0).astype(int)
            if 'half_baths' in df.columns:
                df['half_baths'] = pd.to_numeric(df['half_baths'], errors='coerce').fillna(0).astype(int)

            # Compute region and distance
            df['region'], df['distance_to_city'] = zip(*df.apply(
                lambda row: nearest_region(row['latitude'], row['longitude']), axis=1
            ))

            # Filter by max distance
            df = df[df['distance_to_city'] <= MAX_DISTANCE_KM]
            if df.empty:
                print(f"No listings within {MAX_DISTANCE_KM} kilometers for {city}")
                continue

            df['last_updated'] = datetime.utcnow()
            all_properties.append(df)
            print(f"Scraped {len(df)} listings for {city}")

        except Exception as e:
            print(f"Failed to scrape {city}: {e}")
    
    if not all_properties:
        print("No data scraped. Aborting S3 upload.")
        return False

    # Combine all city data
    combined_df = pd.concat(all_properties, ignore_index=True)

    # Remove duplicate listings based on property URL
    combined_df = combined_df.drop_duplicates(subset='property_url', keep='first')

    # Add sequential ID
    combined_df = combined_df.assign(id=range(1, len(combined_df) + 1))

    # Final columns to include (only those that exist in the DataFrame)
    desired_columns = [
        'id', 'property_url', 'latitude', 'longitude', 'beds', 'full_baths',
        'half_baths', 'list_price', 'formatted_address', 'city', 'region', 'primary_photo'
    ]
    
    # Drop rows missing essential columns (but keep full_baths and half_baths after fillna)
    essential_columns = [col for col in desired_columns if col not in ('full_baths', 'half_baths')]
    combined_df = combined_df.dropna(subset=essential_columns)

    filtered_df = combined_df[[col for col in desired_columns if col in combined_df.columns]]

    # Convert to CSV and upload to S3
    csv_buffer = StringIO()
    filtered_df.to_csv(csv_buffer, index=False)

    try:
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=csv_buffer.getvalue()
        )
        print(f"Successfully uploaded {len(filtered_df)} listings to S3 bucket {s3_bucket} at key {s3_key}.")
        return True
    except Exception as e:
        print(f"Failed to upload to S3: {e}")
        return False

if __name__ == "__main__":
    scrape_and_save_to_s3(
        s3_bucket="commute-rental-listings",
        s3_key="rental_listings.csv"
    )