from sqlalchemy import create_engine
from config.env import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_PORT

db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)