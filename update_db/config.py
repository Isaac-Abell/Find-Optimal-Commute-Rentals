import json
import boto3

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