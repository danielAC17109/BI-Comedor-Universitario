import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def obtener_conexion():

    database_url = os.getenv("DATABASE_URL")

    engine = create_engine(database_url)

    return engine