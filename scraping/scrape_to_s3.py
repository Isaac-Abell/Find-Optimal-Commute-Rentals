import pandas as pd
import boto3
from datetime import datetime
from io import StringIO
from homeharvest import scrape_property
from commute import nearest_region
from config import CITY_CENTERS, MAX_DISTANCE_MILES

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
    
    # Instantiate the S3 client, which will automatically use your local credentials
    s3_client = boto3.client('s3', region_name=region_name)

    for city in CITY_CENTERS.keys():
        print(f"Scraping listings for {city}...")
        try:
            df = scrape_property(
                location=city,
                listing_type="for_rent",
                past_days=7
            )
            
            if df.empty:
                print(f"No listings returned for {city}")
                continue
                
            df = df.dropna(subset=["latitude", "longitude"])
            if df.empty:
                print(f"No valid coordinates for {city}")
                continue
            
            df['region'], df['distance_to_city'] = zip(*df.apply(
                lambda row: nearest_region(row['latitude'], row['longitude']), axis=1
            ))
            
            df = df[df['distance_to_city'] <= MAX_DISTANCE_MILES]
            if df.empty:
                print(f"No listings within {MAX_DISTANCE_MILES} miles for {city}")
                continue
            
            df['last_updated'] = datetime.utcnow()
            
            # --- Fill NaN bathrooms with 0 ---
            for col in ['full_baths', 'half_baths']:
                if col in df.columns:
                    df[col] = df[col].fillna(0)
            
            all_properties.append(df)
            print(f"Scraped {len(df)} listings for {city}")
            
        except Exception as e:
            print(f"Failed to scrape {city}: {e}")
    
    if not all_properties:
        print("No data scraped. Aborting S3 upload.")
        return False
        
    combined_df = pd.concat(all_properties, ignore_index=True)
    
    desired_columns = [
        'property_url', 'latitude', 'longitude', 'beds', 'full_baths',
        'half_baths', 'list_price', 'formatted_address', 'city', 'region'
    ]
    filtered_df = combined_df[[col for col in desired_columns if col in combined_df.columns]]
    filtered_df = filtered_df.assign(id=range(1, len(filtered_df) + 1))
    
    # Use an in-memory buffer to upload to S3
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