import os
from dotenv import load_dotenv
from fastapi import HTTPException
import pyodbc
import logging


# Configurar logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
# Configuración de conexión
def get_connection():
    conn_str = (
        f"DRIVER={{IBM INFORMIX ODBC DRIVER (64-bit)}};"
        f"HOST={os.getenv('DB_HOST')};"
        f"PORT={os.getenv('DB_PORT')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"PROTOCOL={os.getenv('DB_PROTOCOL')};"
    )
    return pyodbc.connect(conn_str)

    
try:
    conn = get_connection()
    cursor = conn.cursor()
except Exception as e:
    logging.error("❌ Error al conectar con la base de datos", exc_info=True)
    raise HTTPException(status_code=500, detail=f"Error al conectar con la base de datos: {e}")