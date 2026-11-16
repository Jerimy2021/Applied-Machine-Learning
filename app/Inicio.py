"""
Página de inicio de la app (Hito 3): qué es el proyecto, el resultado
principal del Hito 2, y el disclaimer de seguridad (repetido también en
la página de predicción, no solo acá).
"""

import streamlit as st
from common import DISCLAIMER, RECALL_IC95, RECALL_TEST

st.set_page_config(page_title="SST: predicción de accidentes", layout="centered")

st.title("Análisis predictivo de accidentes SST")
st.caption("Proyecto del curso de Machine Learning Aplicado, Ingeniería Industrial")

st.markdown(
    """
Clasifica cada accidente reportado como **incapacitante** o **no
incapacitante**, para que el área de SST priorice la atención con
evidencia histórica en vez de solo el criterio del supervisor.
"""
)

col1, col2, col3 = st.columns(3)
col1.metric(
    "Recall en test",
    f"{RECALL_TEST:.3f}",
    help=f"IC 95%: {RECALL_IC95[0]:.3f} - {RECALL_IC95[1]:.3f}",
)
col2.metric("Modelo", "Random Forest")
col3.metric(
    "Población de entrenamiento",
    "828 filas",
    help="Histórico 2019-2022 + 2024, confirmado por SST",
)

st.warning(DISCLAIMER)

st.markdown("### ¿Qué quieres ver?")
st.page_link("pages/1_Resultados_del_modelo.py", label="Resultados del modelo (dashboard)")
st.page_link("pages/2_Hacer_una_prediccion.py", label="Hacer una predicción")

st.divider()
st.caption(
    "Código y documentación completa: "
    "[repositorio en GitHub](https://github.com/Jerimy2021/Applied-Machine-Learning) · "
    "[wiki del proyecto](https://github.com/Jerimy2021/Applied-Machine-Learning/wiki)"
)
