"""
Formulario de predicción en vivo (Hito 3): arma 1 fila con las 8
columnas de X (ver src.prepare.COLUMNAS_X) y la pasa al pipeline final
ya entrenado. Las opciones de cada desplegable salen de
models/categorias_x.json (valores que el modelo vio en train), nunca de
una lista escrita a mano: así nunca se le manda al encoder ya entrenado
una categoría que no conoce.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Streamlit no siempre deja en sys.path el directorio del script
# principal (app/) cuando ejecuta una página de pages/ por separado; se
# agrega a mano para no depender de ese detalle de implementación.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import DISCLAIMER, aplicar_estilos, cargar_categorias, cargar_pipeline  # noqa: E402

st.set_page_config(page_title="Hacer una predicción", layout="centered")
aplicar_estilos()

st.title("Hacer una predicción")
st.caption(
    "Completa los datos de un evento para ver qué predice el modelo "
    "recomendado del Hito 2 (Random Forest, 2019-2022 + 2024)."
)
st.warning(DISCLAIMER)

categorias = cargar_categorias()
pipeline = cargar_pipeline()

with st.form("formulario_prediccion"):
    col_edad, col_turno, col_mes = st.columns(3)
    with col_edad:
        edad_desconocida = st.checkbox("Edad desconocida")
        edad_anios = st.number_input(
            "Edad (años)",
            min_value=int(categorias["edad_anios"]["min"]),
            max_value=int(categorias["edad_anios"]["max"]),
            value=int(categorias["edad_anios"]["mediana"]),
            disabled=edad_desconocida,
        )
    with col_turno:
        turno = st.selectbox("Turno", categorias["categoricas"]["turno"])
    with col_mes:
        mes = st.selectbox("Mes", categorias["categoricas"]["mes"])

    programa = st.selectbox("Programa / sede", categorias["categoricas"]["programa"])
    lugar = st.selectbox("Lugar", categorias["categoricas"]["lugar"])
    puesto_trabajo = st.selectbox("Puesto de trabajo", categorias["categoricas"]["puesto_trabajo"])
    fuente_peligro = st.selectbox("Fuente de peligro", categorias["categoricas"]["fuente_peligro"])
    actividad_realizada = st.selectbox(
        "Actividad realizada", categorias["categoricas"]["actividad_realizada"]
    )

    enviado = st.form_submit_button("Predecir")

if enviado:
    fila = pd.DataFrame(
        [
            {
                "edad_anios": np.nan if edad_desconocida else float(edad_anios),
                "turno": turno,
                "programa": programa,
                "lugar": lugar,
                "puesto_trabajo": puesto_trabajo,
                "fuente_peligro": fuente_peligro,
                "actividad_realizada": actividad_realizada,
                "mes": mes,
            }
        ]
    )

    prediccion = bool(pipeline.predict(fila)[0])
    probabilidades = pipeline.predict_proba(fila)[0]
    indice_true = list(pipeline.classes_).index(True)
    probabilidad_incapacitante = probabilidades[indice_true]

    st.divider()
    if prediccion:
        st.error(f"Predicción: **incapacitante** (probabilidad {probabilidad_incapacitante:.1%})")
    else:
        st.success(
            f"Predicción: **no incapacitante** (probabilidad de incapacitante: "
            f"{probabilidad_incapacitante:.1%})"
        )
    st.caption(DISCLAIMER)
