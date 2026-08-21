"""
Configuración central del proyecto: rutas y constantes.

Todas las rutas se derivan de la raíz del proyecto usando pathlib, para que
el código funcione igual sin importar en qué máquina se ejecute (nada de
rutas absolutas hardcodeadas tipo /Users/<usuario>/...).
"""

from pathlib import Path

# Raíz del proyecto: dos niveles arriba de este archivo (src/config.py -> raíz/)
ROOT_DIR = Path(__file__).resolve().parent.parent

# --- Rutas de datos ---
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"  # Solo lectura. Nunca escribir ni sobrescribir aquí.
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

# --- Rutas de reportes ---
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
DICCIONARIO_DATOS_PATH = REPORTS_DIR / "diccionario_datos.md"

# --- Constantes del proyecto ---
# Nombre de la columna estándar de fecha de evento (ver estándar en CLAUDE.md)
COL_FECHA_EVENTO = "fecha_evento"

# Encoding y formato esperado de los archivos crudos
RAW_FILE_EXTENSION = ".xlsx"
