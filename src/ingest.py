"""
Ingesta de los archivos crudos de accidentes/incidentes SST.

Funciones para cargar los .xlsx de data/raw/ a DataFrames de pandas, y para
guardar los resultados de la limpieza en data/interim/ y data/processed/.
data/raw/ es SOLO LECTURA: load_raw() únicamente lee de ahí, nunca escribe
ni sobrescribe archivos en esa carpeta.
"""

from pathlib import Path

import pandas as pd

from src.clean import anonymize_column, normalize_categorical
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


# --- Carga + limpieza estructural de "Base de Accidentes" (2023 y 2024) ---
#
# Las hojas "Base" de estos dos archivos son las únicas con un registro por
# accidente (los otros 3 archivos de data/raw/ son tableros/indicadores
# agregados). Cada año tiene columnas ligeramente distintas en el Excel
# original, por eso hay un mapeo de renombrado por fuente. Decisiones
# documentadas en reports/diccionario_datos.md:
#   - 2023: se descartan 199 filas de las 306 (residuo de formato de Excel,
#     sin ningún dato real: solo la columna "Sem" venía arrastrada).
#   - Nombres y apellidos se reemplazan por id_persona (hash), nunca se
#     guarda el nombre real en data/interim/ ni data/processed/.
#   - Ningún nulo se imputa: pd.to_numeric/to_datetime con errors="coerce"
#     convierte valores no parseables (ej. "Por confirmar") en NaN, no se
#     inventa ningún valor.

_RENAME_2023 = {
    "Item": "item", "N° ROM": "nro_rom", "PAIS": "pais", "SOCIEDAD": "sociedad",
    "Predio": "predio", "Planta": "planta", "Dirección": "direccion", "Area": "area",
    "Fecha": "fecha_evento", "Sem": "semana", "Día": "dia", "Mes": "mes", "Año": "anio",
    "Hora": "hora", "Turno": "turno", "Tipo de Trabajador": "tipo_trabajador",
    "EMPRESA": "empresa", "SEXO": "sexo", "Edad": "edad_anios",
    "Puesto de Trabajo": "puesto_trabajo",
    "Fecha de Ingreso a Labores": "fecha_ingreso_labores",
    "DESCRIPCION DEL ACCIDENTE": "descripcion_accidente", "Tipo de Contacto": "tipo_contacto",
    "Parte del Cuerpo Afectada": "parte_cuerpo_afectada",
    "Parte del Cuerpo Afectada 2": "parte_cuerpo_afectada_2",
    "Actividad Realizada": "actividad_realizada", "Proceso": "proceso",
    "DIAGNOSTICO": "diagnostico_medico", "Lesión": "lesion", "Dias de D.M.": "dias_dm",
    "Cargo ANSI ": "cargo_ansi", "Dias DM Total Indicador": "dias_dm_total_indicador",
    "Situación Actual": "situacion_actual",
    "Tiempo experiencia\n(meses)": "tiempo_experiencia_meses", "Puesto": "puesto",
    "Antigüedad": "antiguedad", "FUENTE DE PELIGRO": "fuente_peligro",
    "TIPO DE CONTRATO": "tipo_contrato",
}

_RENAME_2024 = {
    "Item": "item", "N° ROM": "nro_rom", "PAIS": "pais",
    "SOCIEDAD\n(Razón Social)": "sociedad", "Predio": "predio",
    "Planta Sigma": "planta_sigma", "Planta": "planta",
    "Dirección de Responsabilidad": "direccion", "Area": "area",
    "Tipo de Accidente": "tipo_accidente", "Tipo de Accidente2": "tipo_accidente_2",
    "Tipo de Accidente3": "tipo_accidente_3", "Fecha\n(XX/XX/2024)": "fecha_evento",
    "Sem": "semana", "Día": "dia", "Mes": "mes", "Año": "anio", "Hora": "hora",
    "Turno": "turno", "Tipo de Trabajador": "tipo_trabajador", "EMPRESA": "empresa",
    "SEXO": "sexo", "Edad": "edad_anios", "Puesto de Trabajo": "puesto_trabajo",
    "Fecha de Ingreso a Labores": "fecha_ingreso_labores",
    "DESCRIPCION DEL ACCIDENTE": "descripcion_accidente", "Tipo de Contacto": "tipo_contacto",
    "Parte del Cuerpo Afectada": "parte_cuerpo_afectada",
    "Parte del Cuerpo Afectada 2": "parte_cuerpo_afectada_2",
    "Actividad Realizada": "actividad_realizada", "DIAGNOSTICO\nMÉDICO": "diagnostico_medico",
    "Lesión": "lesion", "Días DM Total Indicador": "dias_dm_total_indicador",
    "Cargo ANSI ": "cargo_ansi", "Días de D.M.": "dias_dm",
    "Situación Actual": "situacion_actual",
    "Tiempo experiencia\n(meses)": "tiempo_experiencia_meses", "Antigüedad": "antiguedad",
    "FUENTE DE PELIGRO": "fuente_peligro", "TIPO DE CONTRATO": "tipo_contrato",
    "Población": "poblacion",
}

_CATEGORICAL_COLS = [
    "pais", "sociedad", "predio", "planta", "planta_sigma", "direccion", "area",
    "tipo_accidente", "tipo_accidente_2", "tipo_accidente_3", "turno",
    "tipo_trabajador", "empresa", "sexo", "puesto_trabajo", "tipo_contacto",
    "parte_cuerpo_afectada", "parte_cuerpo_afectada_2", "actividad_realizada",
    "proceso", "diagnostico_medico", "lesion", "cargo_ansi", "situacion_actual",
    "puesto", "antiguedad", "fuente_peligro", "tipo_contrato",
]

_COLUMNAS_NUMERICAS = [
    "edad_anios", "dias_dm", "dias_dm_total_indicador",
    "tiempo_experiencia_meses", "semana", "dia", "mes", "anio",
]

_BOOL_MAP = {"SI": True, "SÍ": True, "NO": False}


def _parse_mixed_excel_date(serie: pd.Series) -> pd.Series:
    """
    Parsea una columna de fecha que en el Excel original mezcla celdas con
    formato de fecha (llegan como datetime/Timestamp) con celdas sin ese
    formato (llegan como el número de serie de Excel, un int/float plano).

    pd.to_datetime() interpreta un int plano como nanosegundos desde 1970,
    no como fecha de Excel — por eso primero se convierten los números a
    fecha real (época de Excel: 1899-12-30) antes de parsear el resto.
    """
    def convertir(valor):
        if pd.isna(valor):
            return valor
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=valor)
        return valor

    return pd.to_datetime(serie.apply(convertir), errors="coerce")


def load_base_accidentes(anio: str) -> pd.DataFrame:
    """
    Carga y limpia estructuralmente la "Base" de accidentes de un año
    ("2023" o "2024"): renombra columnas al estándar snake_case, corrige
    problemas propios del archivo fuente, tipa fechas/numéricos, normaliza
    categóricas y reemplaza nombres por un id_persona anonimizado.

    No imputa ningún nulo: solo estructura y tipa. Ver el detalle de cada
    decisión en el comentario de este módulo y en
    reports/diccionario_datos.md.
    """
    if anio == "2023":
        raw = load_raw("Base de Accidentes 2023 _ Total.xlsx", sheet_name="Base")
        raw = raw.loc[raw["Fecha"].notna()].copy()  # descarta residuo de formato
        df = raw.rename(columns=_RENAME_2023)
    elif anio == "2024":
        raw = load_raw("Base Accidentes 2024_Todo Alicorp.xlsx", sheet_name="Base")
        raw = raw.drop(columns=[c for c in raw.columns if c.startswith("Unnamed")])
        df = raw.rename(columns=_RENAME_2024)
        df["es_considerado"] = (
            df["Considerar"].astype("string").str.strip().str.upper().map(_BOOL_MAP)
        )
        # Recategorización solo trae 'SI' cuando aplica, blanco en el resto:
        # se asume blanco == no recategorizado (ver diccionario_datos.md).
        df["es_recategorizado"] = (
            df["Recategorización"].astype("string").fillna("NO").str.strip().str.upper().eq("SI")
        )
        df = df.drop(columns=["Considerar", "Recategorización"])
    else:
        raise ValueError(f"anio debe ser '2023' o '2024', recibido: {anio!r}")

    # Nunca se guarda el nombre real: se reemplaza por un id sintético.
    nombre_completo = (
        df["APELLIDO PATERNO"].astype("string").fillna("")
        + "|" + df["APELLIDO MATERNO"].astype("string").fillna("")
        + "|" + df["NOMBRES"].astype("string").fillna("")
    )
    tmp = anonymize_column(pd.DataFrame({"nombre_completo": nombre_completo}),
                            "nombre_completo", salt="sst-alicorp")
    df["id_persona"] = tmp["nombre_completo"]
    df = df.drop(columns=["APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRES"])

    df["fecha_evento"] = _parse_mixed_excel_date(df["fecha_evento"])
    df["fecha_ingreso_labores"] = _parse_mixed_excel_date(df["fecha_ingreso_labores"])
    for col in _COLUMNAS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in _CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = normalize_categorical(df[col])

    df["fuente_archivo"] = anio
    return df.reset_index(drop=True)
