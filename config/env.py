import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
DB_USER = os.environ.get("username")
DB_PASSWORD = os.environ.get("password")
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT", "5432")