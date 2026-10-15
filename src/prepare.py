"""
Preparación de datos para el modelo de es_incapacitante.

Implementa la estrategia aprobada en reports/estrategia_data_preparation.md:
población de entrenamiento, X final, recodificación de categorías y la
clave de agrupamiento para la partición train/test. Los notebooks solo
importan y muestran (ver CLAUDE.md); nada aquí aprende de los datos, por
eso puede correr antes de separar train y test.
"""

import pandas as pd

from src.clean import derive_es_incapacitante

COLUMNA_NUMERICA = "edad_anios"

COLUMNAS_CATEGORICAS = [
    "turno",
    "programa",
    "lugar",
    "puesto_trabajo",
    "fuente_peligro",
    "actividad_realizada",
    "mes",
]

COLUMNAS_X = [COLUMNA_NUMERICA, *COLUMNAS_CATEGORICAS]

# Grafías duplicadas de la misma categoría, encontradas en
# 03_estadistica_descriptiva (ver reports/estrategia_data_preparation.md,
# sección 3.4). Unificar es una regla fija, no una decisión que dependa de
# los datos de train, así que se aplica antes de la partición.
_GRAFIAS_DUPLICADAS = {
    "mes": {"SETIEMBRE": "SEPTIEMBRE"},
    "actividad_realizada": {"DURANTE RUTINA DE TRABAJO": "DURANTE SU RUTINA DE TRABAJO"},
}

SIN_DATO = "SIN_DATO"


def unificar_grafias(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica las grafías duplicadas de `_GRAFIAS_DUPLICADAS`."""
    df = df.copy()
    for columna, mapa in _GRAFIAS_DUPLICADAS.items():
        if columna in df.columns:
            df[columna] = df[columna].astype("object").replace(mapa).astype("category")
    return df


def recodificar_nulos_categoricos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pasa los nulos de las columnas categóricas de X a la categoría
    explícita `SIN_DATO` (ver estrategia, sección 3.1): es una
    recodificación fija, no una imputación que dependa de train.
    `edad_anios` no se toca aquí, se imputa con la mediana de train dentro
    del pipeline de `src/model.py`.
    """
    df = df.copy()
    for columna in COLUMNAS_CATEGORICAS:
        serie = df[columna]
        if SIN_DATO not in serie.cat.categories:
            serie = serie.cat.add_categories([SIN_DATO])
        df[columna] = serie.fillna(SIN_DATO)
    return df


def cargar_poblacion_modelado(df_historico: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra `accidentes_historico_2012_2022` a la población aprobada para
    entrenar: años 2019-2022 con `es_incapacitante` definido (no `NA`).
    Antes de 2019 el 100% de los registros con etiqueta son incapacitantes
    (ver estrategia, sección 0.A); incluirlos haría que el modelo aprenda
    la época, no el riesgo.
    """
    df = df_historico.copy()
    df["es_incapacitante"] = derive_es_incapacitante(df["gravedad"])
    poblacion = df[(df["anio"] >= 2019) & df["es_incapacitante"].notna()].copy()
    poblacion = unificar_grafias(poblacion)
    poblacion = recodificar_nulos_categoricos(poblacion)
    return poblacion.reset_index(drop=True)


def armar_grupo_evento(df: pd.DataFrame) -> pd.Series:
    """
    Clave de agrupamiento para la partición train/test: filas del mismo
    evento (misma fecha y descripción) van juntas al mismo lado, para no
    separar entre train y test a varios trabajadores afectados por un
    mismo accidente (ver estrategia, sección 3.6). Si la descripción es
    nula, cada fila queda en su propio grupo (no se agrupan nulos entre
    sí por coincidencia).
    """
    fecha = df["fecha_evento"].astype("string").fillna("SIN_FECHA")
    descripcion = df["descripcion_accidente"].astype("string")
    descripcion = descripcion.fillna("fila_" + df.index.to_series().astype("string"))
    return fecha + "||" + descripcion


def armar_X_y(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Separa X (`COLUMNAS_X`) e y (`es_incapacitante`, bool) de la población de modelado."""
    X = df[COLUMNAS_X].copy()
    y = df["es_incapacitante"].astype(bool)
    return X, y


_NOMBRE_MES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
    7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE",
}

COLUMNAS_COMUNES_MODELADO = [
    *COLUMNAS_X, "es_incapacitante", "fecha_evento", "descripcion_accidente"
]


def cargar_poblacion_2024_experimental(df_2024: pd.DataFrame) -> pd.DataFrame:
    """
    EXPERIMENTAL, no es el target oficial del Hito 2 (ver notebook
    04_modelado, sección "Experimento adicional").

    `accidentes_2024.csv` no trae `gravedad`, así que no se puede derivar
    `es_incapacitante` con `derive_es_incapacitante()`. Se usa como proxy
    `dias_dm > 0`: esa equivalencia se verificó para el histórico
    2019-2022 (coincide con la etiqueta real en 458 de 459 filas, ver
    reports/estrategia_data_preparation.md), pero **no está confirmada por
    el equipo de SST específicamente para esta fuente** — queda como
    pendiente explícito, no se oculta el supuesto.

    `programa` y `lugar` no existen en este archivo (el Excel original no
    las traía): quedan en `SIN_DATO` en todas las filas de 2024, igual que
    cualquier otro nulo categórico. `mes` viene como número (1-12) en vez
    de nombre; convertirlo es una traducción exacta de calendario, no una
    equivalencia de negocio. El código de `turno` de esta fuente (`D`,
    `M`, `N`, `T`, `C`) es distinto al del histórico (`DIA`, `TARDE`,
    `NOCHE`, `TURNO_1/2/3`) y **no se intenta unificar**: no hay forma de
    confirmar sin adivinar qué significa cada letra (en particular `M` y
    `C`), mismo criterio que ya se aplicó para no unificar el turno
    numerado con el de franja horaria en el histórico.
    """
    df = df_2024.copy()
    df = df[df["dias_dm"].notna()].copy()
    df["es_incapacitante"] = df["dias_dm"] > 0

    df["mes"] = df["mes"].map(_NOMBRE_MES)
    df["programa"] = pd.NA
    df["lugar"] = pd.NA

    for columna in COLUMNAS_CATEGORICAS:
        serie = df[columna].astype("string").replace("-", pd.NA)
        df[columna] = serie.astype("category")

    df = recodificar_nulos_categoricos(df)
    return df.reset_index(drop=True)


def combinar_con_2024(
    poblacion_historico: pd.DataFrame, poblacion_2024: pd.DataFrame
) -> pd.DataFrame:
    """Concatena el histórico 2019-2022 con la salida de `cargar_poblacion_2024_experimental`."""
    return pd.concat(
        [poblacion_historico[COLUMNAS_COMUNES_MODELADO], poblacion_2024[COLUMNAS_COMUNES_MODELADO]],
        ignore_index=True,
    )
