import pandas as pd
import boto3
from io import StringIO
from sqlalchemy import text
from db import engine

def lambda_handler(event, context):
    """
    Reads a CSV file from S3 and replaces the 'listings' table in PostgreSQL.
    s3_key (str): The object key (path and filename) for the CSV in S3.

    Returns:
        bool: True if the database was updated, False otherwise.
    """
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_key = event['Records'][0]['s3']['object']['key']
    
    s3_client = boto3.client('s3')
    try:
        obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        csv_string = obj['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_string))
    except Exception as e:
        print(f"Failed to read file from S3: {e}")
        return False

    print(f"Adding {len(df)} records to the database...")
    try:
        with engine.begin() as conn:
            df.to_sql(
                'listings',
                conn,
                schema='public',
                if_exists='replace',
                index=False
            )
            
            conn.execute(text("ALTER TABLE public.listings ADD PRIMARY KEY (id);"))
            
        print(f"Database table 'listings' replaced with {len(df)} rental listings.")
        return True
    except Exception as e:
        print(f"Failed to insert data into the database: {e}")
        return False