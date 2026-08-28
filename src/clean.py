"""
Limpieza y normalización de la data de accidentes/incidentes SST.

Funciones reutilizables de limpieza (renombrado de columnas al estándar
snake_case, normalización de categóricas, parseo de fechas, etc.).

Toda decisión de limpieza (imputación, eliminación, recodificación) debe
quedar registrada con su justificación en reports/diccionario_datos.md antes
de aplicarse aquí. Prohibido imputar silenciosamente: report_nulls() solo
reporta, nunca rellena — la decisión de qué hacer con cada nulo se toma y
documenta primero, y se implementa después como un paso explícito.
"""

import hashlib

import pandas as pd


def report_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reporta nulos por columna (cantidad y % sobre el total de filas).

    No imputa nada. Usar el resultado para llenar la sección "Nulos
    detectados" de reports/diccionario_datos.md y decidir ahí qué hacer con
    cada columna antes de escribir la función de limpieza correspondiente.
    """
    n_nulos = df.isna().sum()
    pct_nulos = (n_nulos / len(df) * 100).round(2)
    reporte = pd.DataFrame({"n_nulos": n_nulos, "pct_nulos": pct_nulos})
    return reporte[reporte["n_nulos"] > 0].sort_values("n_nulos", ascending=False)


def anonymize_column(df: pd.DataFrame, column: str, salt: str = "") -> pd.DataFrame:
    """
    Reemplaza los valores de una columna sensible (nombres, DNI, legajos) por
    un ID sintético (hash SHA-256 truncado a 12 caracteres). El mismo valor
    original siempre produce el mismo ID, para poder seguir cruzando tablas
    sin exponer el dato real.

    No modifica el DataFrame recibido: devuelve una copia.

    Documentar en reports/diccionario_datos.md (sección "Anonimización") cada
    columna a la que se le aplica esta función.
    """
    def _hash(valor):
        if pd.isna(valor):
            return valor  # un nulo sigue siendo nulo, no se "anonimiza" a un hash
        return hashlib.sha256((salt + str(valor)).encode("utf-8")).hexdigest()[:12]

    df = df.copy()
    df[column] = df[column].apply(_hash)
    return df


# TODO: funciones de limpieza específicas (normalización de columnas a
# snake_case, dtypes, categorías en MAYÚSCULAS, parseo de fecha_evento, etc.)
# se agregan aquí a medida que se aprueban en reports/diccionario_datos.md.
