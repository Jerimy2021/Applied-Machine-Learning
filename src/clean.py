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
import re
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


_PATRON_ID_ETIQUETADO = re.compile(r"\b(DNI|RUC)\b[\s:.\-]*\d{6,11}", re.IGNORECASE)
_PATRON_NOMBRE_PROPIO = re.compile(
    r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}\b"
)


def redact_pii_libre(serie: pd.Series) -> pd.Series:
    """
    Enmascara, en una columna de texto libre (ej. `descripcion_accidente`),
    dos patrones que probablemente son datos personales:
      - DNI/RUC etiquetados explícitamente (ej. "DNI 09065660") -> "[DNI]"/"[RUC]"
      - Secuencias de 2 a 4 palabras en Título-Caso (candidato a nombre
        propio, ej. "Ysmael Pinares Vargas") -> "[NOMBRE]"

    **Es una heurística de primera pasada, no un NER validado** (ver
    reports/diccionario_datos.md):
      - Puede enmascarar nombres de lugar/clínica/empresa que también están
        en Título-Caso (falso positivo, ej. "Molino Santa Rosa"). Se
        prioriza no dejar pasar un nombre de persona sobre preservar esos
        términos.
      - Puede no detectar un nombre que no siga el patrón esperado (una sola
        palabra, todo minúsculas, etc. — falso negativo).
    No reemplaza una revisión humana antes de compartir esta columna fuera
    del equipo.
    """
    def _enmascarar(valor):
        if pd.isna(valor):
            return valor
        texto = _PATRON_ID_ETIQUETADO.sub(lambda m: f"[{m.group(1).upper()}]", str(valor))
        texto = _PATRON_NOMBRE_PROPIO.sub("[NOMBRE]", texto)
        return texto

    return serie.apply(_enmascarar)


_MAPA_TURNO = {
    # Sinónimos de turno numerado (mismo esquema, distinta redacción).
    "1RO": "TURNO_1", "1": "TURNO_1", "1ERO": "TURNO_1", "1ER": "TURNO_1",
    "1ER TURNO": "TURNO_1",
    "2DO": "TURNO_2", "2": "TURNO_2", "2NDO": "TURNO_2", "2DO TURNO": "TURNO_2",
    "2RO": "TURNO_2",
    "3RO": "TURNO_3", "3": "TURNO_3", "3ER": "TURNO_3",
    # Sinónimos dentro de la misma franja horaria (no del esquema numerado).
    "MANANA": "DIA",
    "MADRUGADA": "NOCHE", "MEDIA NOCHE": "NOCHE",
    # Marcador de "no reportado", mismo criterio que en sexo/gravedad.
    "-": pd.NA,
}


def normalize_turno(serie: pd.Series) -> pd.Series:
    """
    Agrupa los sinónimos de la columna `turno` de
    `accidentes_historico_2012_2022.csv` en 6 categorías finales: `TURNO_1`,
    `TURNO_2`, `TURNO_3` (turno numerado — ej. "1RO"/"1ER"/"1ER TURNO" son la
    misma cosa escrita distinto) y `DIA`, `TARDE`, `NOCHE` (franja horaria —
    "MANANA" se une a `DIA`; "MADRUGADA"/"MEDIA NOCHE" se unen a `NOCHE`).

    **Decisión explícita del equipo**: NO se asume que un turno numerado
    corresponda a una franja horaria (ej. turno 1 = DIA) — sería inventar una
    equivalencia de negocio no verificable con la data disponible, así que
    ambos esquemas quedan como categorías separadas. `"-"` se trata como
    nulo (mismo criterio que en `sexo`/`gravedad`). Ver
    reports/diccionario_datos.md.

    Espera una serie ya pasada por `normalize_categorical` (mayúsculas, sin
    tildes). Cualquier valor no reconocido en el mapeo (incluido `NaN`) se
    deja tal cual, no se descarta silenciosamente.
    """
    limpio = serie.astype("string").map(
        lambda v: _MAPA_TURNO.get(v, v) if pd.notna(v) else v
    )
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
