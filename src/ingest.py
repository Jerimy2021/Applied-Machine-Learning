"""
Ingesta de los archivos crudos de accidentes/incidentes SST.

Funciones para cargar los .xlsx de data/raw/ a DataFrames de pandas, y para
guardar los resultados de la limpieza en data/interim/ y data/processed/.
data/raw/ es SOLO LECTURA: load_raw() únicamente lee de ahí, nunca escribe
ni sobrescribe archivos en esa carpeta.
"""

from pathlib import Path

import pandas as pd

from src.config import INTERIM_DIR, PROCESSED_DIR, RAW_DIR


def load_raw(filename: str, sheet_name: int | str = 0, **read_excel_kwargs) -> pd.DataFrame:
    """
    Carga un archivo de data/raw/ a un DataFrame. Solo lee: nunca escribe ni
    modifica nada dentro de data/raw/.

    Parameters
    ----------
    filename : nombre exacto del archivo dentro de data/raw/
        (ej. "Base de Accidentes 2023 _ Total.xlsx").
    sheet_name : hoja a cargar (índice o nombre). Por defecto la primera.
    **read_excel_kwargs : argumentos extra para pandas.read_excel
        (ej. header=1 si el encabezado no está en la primera fila).
    """
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró '{filename}' en {RAW_DIR}. ¿Está el nombre exacto y en data/raw/?"
        )
    return pd.read_excel(path, sheet_name=sheet_name, **read_excel_kwargs)


def save_interim(df: pd.DataFrame, name: str) -> Path:
    """
    Guarda un resultado intermedio (un paso parcial de limpieza, todavía no
    aprobado/anonimizado) en data/interim/<name>.csv.

    data/interim/ NUNCA se commitea (no tiene excepción en .gitignore) —
    úsala libremente como espacio de trabajo entre data/raw/ y data/processed/.
    """
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out_path = INTERIM_DIR / f"{name}.csv"
    df.to_csv(out_path, index=False)
    return out_path


def save_processed(df: pd.DataFrame, name: str) -> Path:
    """
    Guarda el resultado final en data/processed/<name>.csv.

    IMPORTANTE: los CSV de data/processed/ SÍ se pueden commitear (única
    excepción en .gitignore). Antes de llamar a esta función, confirmar que
    `df` ya pasó por clean.anonymize_column() en toda columna con nombres,
    DNI o legajos — ver CONTRIBUTING.md.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / f"{name}.csv"
    df.to_csv(out_path, index=False)
    return out_path
