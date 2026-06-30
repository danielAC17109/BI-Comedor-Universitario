import os
import pyodbc

from dotenv import load_dotenv

load_dotenv()

def obtener_conexion():

    conexion = pyodbc.connect(

        f"DRIVER={{{os.getenv('DB_DRIVER')}}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"Trusted_Connection={os.getenv('DB_TRUSTED')};"

    )

    return conexion