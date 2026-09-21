from sqlalchemy import create_engine, URL
from dotenv import load_dotenv
import os

load_dotenv()

url = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password=os.getenv("DB_PASSWORD"),
    host="localhost",
    port=5432,
    database="task_manager"
)

engine = create_engine(url)