"""
Ingesta de los archivos crudos de accidentes/incidentes SST.

Funciones para cargar los .xlsx de data/raw/ a DataFrames de pandas, y para
guardar los resultados de la limpieza en data/interim/ y data/processed/.
data/raw/ es SOLO LECTURA: load_raw() únicamente lee de ahí, nunca escribe
ni sobrescribe archivos en esa carpeta.
"""

from pathlib import Path

import pandas as pd

from src.clean import anonymize_column, normalize_categorical, normalize_turno, redact_pii_libre
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

    dayfirst=True porque las fechas en texto libre del Excel original están
    en formato peruano (DD/MM/AAAA). Algunas celdas están mal escritas (año
    a 2 dígitos, mes inválido, dígitos de más) — con errors="coerce" esas
    quedan como NaT en vez de adivinar una fecha.
    """
    def convertir(valor):
        if pd.isna(valor):
            return valor
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=valor)
        return valor

    return pd.to_datetime(serie.apply(convertir), errors="coerce", dayfirst=True)


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
            df["Considerar"].astype("string").str.strip().str.upper()
            .map(_BOOL_MAP).astype("boolean")
        )
        # Recategorización solo trae 'SI' cuando aplica, blanco en el resto:
        # se asume blanco == no recategorizado (ver diccionario_datos.md).
        df["es_recategorizado"] = (
            df["Recategorización"].astype("string").fillna("NO").str.strip().str.upper()
            .eq("SI").astype("boolean")
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
    df["descripcion_accidente"] = redact_pii_libre(df["descripcion_accidente"])

    # Valor imposible por regla de negocio verificable (no un umbral
    # arbitrario): nadie puede tener más años de experiencia que de vida. Se
    # marca como NA, no se imputa ningún reemplazo. Ver diccionario_datos.md,
    # sección "Valores atípicos".
    imposible = (df["tiempo_experiencia_meses"] / 12) > df["edad_anios"]
    df.loc[imposible, "tiempo_experiencia_meses"] = pd.NA

    df["fuente_archivo"] = anio
    return df.reset_index(drop=True)


# --- Carga + limpieza estructural de las 3 fuentes adicionales ---
#
# Además de las 2 "Base" (2023/2024), otros 3 archivos de data/raw/ resultaron
# tener registros fila-por-accidente/incidente y no solo indicadores
# agregados:
#   - "Resultados SST 2023 v06final.xlsx" / hoja "HISTORICO ACCIDENTES":
#     accidentes 2012-2022 (fila por accidente).
#   - "Tablero de Accidentes e incidentes.xlsx" / hoja "2° Accidentes":
#     accidentes 2025-2026.
#   - "Tablero de Accidentes e incidentes.xlsx" / hoja "1° Incidentes":
#     incidentes (no accidentes) 2025-2026.
# Cada una tiene su propio esquema de columnas, distinto al de 2023/2024, por
# eso se guardan como archivos separados en vez de forzar un merge. Decisiones
# documentadas en reports/diccionario_datos.md.

_RENAME_HISTORICO = {
    "ROM": "nro_rom", "PROGRAMA": "programa", "LUGAR": "lugar",
    "AREA RESPONSABILIDAD": "area_responsabilidad", "Edad": "edad_anios",
    "Puesto de Trabajo": "puesto_trabajo", "SEXO": "sexo", "TURNO": "turno",
    "Experiencia en el Puesto Trabajo": "experiencia_puesto",
    "Fecha": "fecha_evento", "GG": "gravedad",
    "Descripción del Accidente de Trabajo": "descripcion_accidente",
    "Parte Cuerpo": "parte_cuerpo_afectada", "Año": "anio", "Mes": "mes",
    "Días Perdidos x Lesión": "dias_perdidos", "Cargo ANSI": "cargo_ansi",
    "Dias + ansi": "dias_mas_ansi", "FUENTE PELIGRO": "fuente_peligro",
    "Actividad": "actividad_realizada", "TIPO DE CONTACTO": "tipo_contacto",
    "DAÑO": "dano", "Contrata": "contrata", "NOTA MIDOT": "nota_midot",
    "MODALIDAD": "modalidad",
}

_CATEGORICAL_COLS_HISTORICO = [
    "programa", "lugar", "area_responsabilidad", "puesto_trabajo", "sexo",
    "turno", "gravedad", "parte_cuerpo_afectada", "mes", "cargo_ansi",
    "fuente_peligro", "actividad_realizada", "tipo_contacto", "dano",
    "contrata", "modalidad",
]

_COLUMNAS_NUMERICAS_HISTORICO = ["edad_anios", "dias_perdidos", "dias_mas_ansi", "nota_midot"]

# 3 celdas de "HISTORICO ACCIDENTES" quedaron mal pegadas: traen el mismo
# texto que la columna GG (gravedad) de esa misma fila, no un valor propio de
# su columna. Confirmado fila por fila que NO es un corrimiento de columnas
# (el resto de cada fila tiene valores normales para su propia columna) —
# ver bitácora en reports/diccionario_datos.md. Se marcan como NA solo esas
# celdas puntuales, se conserva el resto de la fila.
# (índice de fila, columna renombrada) según el índice original del Excel.
_CELDAS_CONTAMINADAS_HISTORICO = [
    (12, "experiencia_puesto"),
    (36, "experiencia_puesto"),
    (920, "turno"),
]

# PII real (nombre completo de una persona, en un caso junto a su RUC) que
# quedó en columnas que no son de identidad (`area_responsabilidad`,
# `contrata`), detectado en una auditoría de PII sobre las 5 fuentes
# procesadas. Se limpia solo la celda puntual — ver bitácora en
# reports/diccionario_datos.md. (Un 6to caso encontrado en la auditoría,
# "Casimiro Villacres Taiwan" en `area_responsabilidad`, no se incluye aquí
# porque su fila tiene anio=2023 y ya queda excluida por el filtro de año de
# esta función — no llega a estar en el CSV final.)
_CELDAS_PII_HISTORICO = [
    (868, "area_responsabilidad"),  # "De La Cruz Rojas,Bladimir Marco"
    (874, "area_responsabilidad"),  # "Doroteo Rodriguez Liz Melissa"
    (873, "area_responsabilidad"),  # "Perez Ambrosio Leandro Estefano"
    (974, "area_responsabilidad"),  # "La Rosa Lescano Gerald Gil"
    (867, "area_responsabilidad"),  # "Ricardo Corrales Valqui"
    (805, "contrata"),  # "Francisco Serpa Vega (RUC 1008276111)"
    (312, "contrata"),  # "Juan Carlos Echegaray (Transp)"
    (367, "contrata"),  # ": Rodriguez Flores Juan Luis (Concesionario)"
]

_RENAME_TABLERO_ACCIDENTES = {
    "N° de ROM": "nro_rom", "SOCIEDAD2": "sociedad", "VP": "vicepresidencia",
    "DIRECCIÓN": "direccion", "CATEGORÍA": "categoria",
    "PLANTA DE OCURRENCIA": "planta", "PLANTA SIGMA": "planta_sigma",
    "FECHA": "fecha_evento", "HORA DE OCURRENCIA": "hora", "TURNO": "turno",
    "DIA DE SEMANA": "dia_semana", "EDAD DEL ACCIDENTADO": "edad_anios",
    "TIEMPO EN LA EMPRESA (meses)": "tiempo_empresa_meses",
    "TIEMPO EN LA EMPRESA (años)": "tiempo_empresa_anios",
    "CANTIDAD DE HORAS TRABAJADAS EN EL TURNO": "horas_trabajadas_turno",
    "ÁREA DEL ACCIDENTADO": "area", "EMPRESA": "empresa",
    "Tipo de Trabajador": "tipo_trabajador", "DESCRIPCIÓN": "descripcion_accidente",
    "LESIÓN": "lesion", "DÍAS REGISTRABLES": "dias_registrables",
    "FUENTE DE PELIGRO": "fuente_peligro",
    "CAUSA BASICA (SEGÚN SCAT)": "causa_basica", "CAUSA PRINCIPAL": "causa_principal",
    "CAUSA INMEDIATA": "causa_inmediata", "TRIMESTRE": "trimestre",
    "¿Se realizó\n el Hard Stop?": "es_hard_stop",
}

_CATEGORICAL_COLS_TABLERO_ACCIDENTES = [
    "sociedad", "vicepresidencia", "direccion", "categoria", "planta",
    "planta_sigma", "turno", "dia_semana", "area", "empresa",
    "tipo_trabajador", "lesion", "fuente_peligro", "causa_basica",
    "causa_principal", "causa_inmediata", "trimestre",
]

# Columnas descartadas de "2° Accidentes": contadores/artefactos de Excel
# (Unnamed, T1/T2, "DIAS SEGUROS") o preguntas de seguimiento con códigos
# mixtos (no SI/NO limpio) que no se pudieron interpretar con confianza —
# ver bitácora en reports/diccionario_datos.md.
_DROP_COLS_TABLERO_ACCIDENTES = [
    "Unnamed: 0", "DIAS SEGUROS", "Turno", "Unnamed: 32", "T1", "T1.1", "T2", "T2.1",
    "¿La Investigación está  cerrada?", "¿Tiene\n ROM?",
    "¿Se difundieron\n las lecciones aprendidas?", "¿Se difundió en el espacio diario?",
    "Unnamed: 42", "Unnamed: 43",
]

_RENAME_INCIDENTES = {
    "Planta": "planta", "Fecha": "fecha_evento", "EMPRESA": "empresa",
    "Tipo de evento": "tipo_evento", "Descripción": "descripcion_incidente",
    "Daños reales o potenciales": "danos_reales_o_potenciales",
    "Fuente de peligro": "fuente_peligro", "verificado": "es_verificado",
}

_CATEGORICAL_COLS_INCIDENTES = ["planta", "empresa", "tipo_evento", "fuente_peligro"]


def load_historico_accidentes() -> pd.DataFrame:
    """
    Carga y limpia la hoja "HISTORICO ACCIDENTES" de
    "Resultados SST 2023 v06final.xlsx": accidentes de 2012 a 2022, un
    accidente por fila.

    Se excluye 2023 en adelante para no duplicar los registros que ya vienen
    de `load_base_accidentes("2023")` / ("2024"). Algunas fechas del Excel
    original están mal escritas (año a 2 dígitos, mes inválido, etc.) — se
    convierten a `NaT` (`errors="coerce"` dentro de `_parse_mixed_excel_date`),
    no se intenta adivinar la fecha real. Ver reports/diccionario_datos.md.
    """
    raw = load_raw("Resultados SST 2023 v06final.xlsx", sheet_name="HISTORICO ACCIDENTES")
    raw.columns = raw.columns.str.strip()
    df = raw.rename(columns=_RENAME_HISTORICO)

    # Celdas mal pegadas (ver constante arriba): se limpia solo la celda, no la fila.
    for fila, columna in _CELDAS_CONTAMINADAS_HISTORICO:
        df.loc[fila, columna] = pd.NA

    # PII real en columnas que no son de identidad (ver constante arriba).
    for fila, columna in _CELDAS_PII_HISTORICO:
        df.loc[fila, columna] = pd.NA

    # Nunca se guarda el nombre real: se reemplaza por un id sintético.
    df = anonymize_column(df, "NOMBRE", salt="sst-alicorp")
    df = df.rename(columns={"NOMBRE": "id_persona"})

    df["fecha_evento"] = _parse_mixed_excel_date(df["fecha_evento"])
    for col in _COLUMNAS_NUMERICAS_HISTORICO:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in _CATEGORICAL_COLS_HISTORICO:
        df[col] = normalize_categorical(df[col])
    df["descripcion_accidente"] = redact_pii_libre(df["descripcion_accidente"])
    df["turno"] = normalize_turno(df["turno"])

    # Valores imposibles por regla de negocio, no umbral arbitrario. Se
    # marcan como NA, no se imputa ningún reemplazo. Ver diccionario_datos.md,
    # sección "Valores atípicos".
    df.loc[df["edad_anios"] <= 0, "edad_anios"] = pd.NA
    df.loc[df["dias_perdidos"] == 6000, "dias_perdidos"] = pd.NA
    df.loc[df["dias_mas_ansi"] == 6000, "dias_mas_ansi"] = pd.NA

    df["fuente_archivo"] = "historico_2012_2022"
    df = df[df["anio"] < 2023].reset_index(drop=True)
    return df


def load_accidentes_tablero() -> pd.DataFrame:
    """
    Carga y limpia la hoja "2° Accidentes" de
    "Tablero de Accidentes e incidentes.xlsx": accidentes 2025-2026, un
    accidente por fila.

    El encabezado real está en la fila 2 del Excel (`header=1`). Apellidos +
    nombre + DNI (todo PII) se combinan y se reemplazan por `id_persona`
    antes de descartar esas 3 columnas.
    """
    raw = load_raw(
        "Tablero de Accidentes e incidentes.xlsx", sheet_name="2° Accidentes", header=1
    )
    raw.columns = raw.columns.str.strip()
    raw = raw.dropna(how="all").reset_index(drop=True)
    raw = raw.drop(columns=[c for c in _DROP_COLS_TABLERO_ACCIDENTES if c in raw.columns])

    dni_texto = raw["DNI"].apply(lambda v: "" if pd.isna(v) else str(int(v)))
    nombre_completo = (
        raw["APELLIDOS DEL ACCIENTADO"].astype("string").fillna("")
        + "|" + raw["NOMBRE DEL ACCIDENTADO"].astype("string").fillna("")
        + "|" + dni_texto
    )
    raw = raw.drop(columns=["APELLIDOS DEL ACCIENTADO", "NOMBRE DEL ACCIDENTADO", "DNI"])

    df = raw.rename(columns=_RENAME_TABLERO_ACCIDENTES)
    tmp = anonymize_column(
        pd.DataFrame({"nombre_completo": nombre_completo}), "nombre_completo", salt="sst-alicorp"
    )
    df["id_persona"] = tmp["nombre_completo"]

    df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    df["es_hard_stop"] = (
        df["es_hard_stop"].astype("string").str.strip().str.upper()
        .map(_BOOL_MAP).astype("boolean")
    )
    for col in _CATEGORICAL_COLS_TABLERO_ACCIDENTES:
        if col in df.columns:
            df[col] = normalize_categorical(df[col])
    df["descripcion_accidente"] = redact_pii_libre(df["descripcion_accidente"])

    df["fuente_archivo"] = "tablero_2025_2026"
    return df.reset_index(drop=True)


def load_incidentes() -> pd.DataFrame:
    """
    Carga y limpia la hoja "1° Incidentes" de
    "Tablero de Accidentes e incidentes.xlsx": incidentes (no accidentes)
    2025-2026, un incidente por fila.

    A diferencia de las demás fuentes, esta hoja no trae nombre/apellido/DNI
    de ninguna persona — no requiere anonimización.
    """
    raw = load_raw(
        "Tablero de Accidentes e incidentes.xlsx", sheet_name="1° Incidentes ", header=1
    )
    raw.columns = raw.columns.str.strip()
    raw = raw.dropna(how="all").reset_index(drop=True)
    df = raw.rename(columns=_RENAME_INCIDENTES)

    df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    df["es_verificado"] = (
        df["es_verificado"].astype("string").str.strip().str.upper()
        .map(_BOOL_MAP).astype("boolean")
    )
    for col in _CATEGORICAL_COLS_INCIDENTES:
        df[col] = normalize_categorical(df[col])
    df["descripcion_incidente"] = redact_pii_libre(df["descripcion_incidente"])
    df["danos_reales_o_potenciales"] = redact_pii_libre(df["danos_reales_o_potenciales"])

    df["fuente_archivo"] = "tablero_2025_2026"
    return df.reset_index(drop=True)
