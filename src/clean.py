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
import unicodedata

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


def strip_accents(texto: str) -> str:
    """Quita tildes/diacríticos de un texto (ej. 'Área' -> 'Area')."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def normalize_categorical(serie: pd.Series) -> pd.Series:
    """
    Normaliza una columna categórica al estándar de CLAUDE.md: sin espacios
    sobrantes, MAYÚSCULAS, sin tildes, dtype 'category'. Un string vacío
    tras el strip se trata como nulo (no como una categoría propia).
    """
    limpio = (
        serie.astype("string")
        .str.strip()
        .apply(lambda v: strip_accents(v).upper() if pd.notna(v) else v)
    )
    limpio = limpio.replace("", pd.NA)
    return limpio.astype("category")


def derive_es_incapacitante(gravedad: pd.Series) -> pd.Series:
    """
    Deriva la etiqueta booleana `es_incapacitante` a partir de la columna
    `gravedad` de `accidentes_historico_2012_2022.csv` (única fuente que la
    trae). Reglas acordadas con el equipo (ver reports/diccionario_datos.md,
    sección "Variable objetivo"):

      - Contiene "INCAPACITANTE" sin "NO " inmediatamente antes -> True
      - Contiene "NO INCAPACITANTE" -> False
      - Contiene "INCIDENTE" (incluida la variante mal escrita "INCICENTE")
        -> False
      - Cualquier otro valor (incl. "-", nulo, y los 2 casos pendientes de
        revisión caso a caso "ACCIDENTE FUERA DEL TRABAJO" y
        "DAÑO A LA SALUD") -> `pd.NA`. No se imputa ni se adivina.

    Espera `gravedad` ya normalizada por `normalize_categorical` (mayúsculas,
    sin tildes) — igual funciona si no lo está, salvo por tildes.
    """
    def _clasificar(valor):
        if pd.isna(valor):
            return pd.NA
        # Colapsa espacios múltiples (el dato original trae, ej., "DANO   A LA SULUD").
        texto = " ".join(str(valor).split())
        if "NO INCAPACITANTE" in texto:
            return False
        if "INCAPACITANTE" in texto:
            return True
        if "INCIDENTE" in texto or "INCICENTE" in texto:
            return False
        return pd.NA

    return gravedad.apply(_clasificar).astype("boolean")
