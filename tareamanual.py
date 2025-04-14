import requests 
from datetime import datetime, timedelta
import os
import json
import shutil
import logging
from dotenv import load_dotenv

# Configuración de logging
# Configuración de logs
log_path = "logs/tareamanual.log"
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("API_TOKEN")

# URL de la API
API_URL = "http://localhost:8000/pacientes"

# Carpeta local donde se guardarán los archivos JSON
CARPETA_LOCAL = "resultados"
os.makedirs(CARPETA_LOCAL, exist_ok=True)

# Ruta de destino final del archivo (ajústala según tu necesidad)
RUTA_DESTINO = "C:/respaldos/json/"
os.makedirs(RUTA_DESTINO, exist_ok=True)

# Calcular fechas del mes anterior
def calcular_fechas_mes_anterior():
    hoy = datetime.today()
    primer_dia_mes_actual = datetime(hoy.year, hoy.month, 1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = datetime(ultimo_dia_mes_anterior.year, ultimo_dia_mes_anterior.month, 1)
    
    fecha_inicio = primer_dia_mes_anterior.strftime("%Y-%m-%d")
    fecha_fin = ultimo_dia_mes_anterior.strftime("%Y-%m-%d")
    return fecha_inicio, fecha_fin, primer_dia_mes_anterior.year, primer_dia_mes_anterior.month

# Ejecutar consulta a la API
def ejecutar_consulta():
    fecha_inicio, fecha_fin, anio, mes = calcular_fechas_mes_anterior()

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    params = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }

    try:
        logging.info(f"Ejecutando consulta para rango: {fecha_inicio} a {fecha_fin}")
        print("Ejecutando tarea Manual")
        response = requests.get(API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            nombre_archivo = f"pacientes_{anio}_{str(mes).zfill(2)}.json"
            ruta_archivo_local = os.path.join(CARPETA_LOCAL, nombre_archivo)

            # Guardar localmente
            with open(ruta_archivo_local, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"Datos guardados localmente en: {ruta_archivo_local}")
            print("Datos Guardados Localmente")

            # Copiar a ruta destino
            ruta_destino_completa = os.path.join(RUTA_DESTINO, nombre_archivo)
            shutil.copy(ruta_archivo_local, ruta_destino_completa)
            logging.info(f"Archivo copiado a: {ruta_destino_completa}")
            print("Archivo Copiado en la Ruta Establecida")

        else:
            logging.error(f"Error en la API: {response.status_code} - {response.text}")
            print("Error en la API, validar servicios")
    except Exception as e:
        logging.exception(f"Error ejecutando la tarea: {str(e)}")
        print("Error en la ejecucion de la tarea manual")

# Llamar directamente para pruebas
if __name__ == "__main__":
    ejecutar_consulta()