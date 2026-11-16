"""
Página de inicio de la app (Hito 3): qué es el proyecto, el resultado
principal del Hito 2, y el disclaimer de seguridad (repetido también en
la página de predicción, no solo acá).
"""

import streamlit as st
from common import DISCLAIMER, RECALL_IC95, RECALL_TEST, aplicar_estilos

st.set_page_config(page_title="SST: predicción de accidentes", layout="centered")
aplicar_estilos()

st.title("Análisis predictivo de accidentes SST")
st.caption("Proyecto del curso de Machine Learning Aplicado, Ingeniería Industrial")

# Numero grande primero (lo que mas importa, no una metrica chica mas
# entre otras tres): ver el "antes/ahora" de abajo para el porque.
st.markdown(
    f"""
    <div class="hero-stat">
        <div class="hero-stat-numero">{RECALL_TEST:.1%}</div>
        <div class="hero-stat-etiqueta">
            de los accidentes <strong>no incapacitantes</strong> se identifican
            correctamente (recall en test, IC 95%: {RECALL_IC95[0]:.1%}-{RECALL_IC95[1]:.1%})
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_antes, col_ahora = st.columns(2)
with col_antes:
    st.markdown("**Antes**")
    st.caption(
        "Priorizar la atención de un accidente dependía solo del criterio "
        "del supervisor, sin evidencia histórica que lo respaldara."
    )
with col_ahora:
    st.markdown("**Ahora**")
    st.caption(
        "Un modelo entrenado con 828 accidentes reales (2019-2022 + 2024, "
        "confirmados por SST) respalda esa decisión con datos."
    )

st.divider()

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
col_dashboard, col_prediccion = st.columns(2)
with col_dashboard:
    st.page_link("pages/1_Resultados_del_modelo.py", label="Resultados del modelo (dashboard)")
with col_prediccion:
    st.page_link("pages/2_Hacer_una_prediccion.py", label="Hacer una predicción")

st.divider()
st.caption(
    "Código y documentación completa: "
    "[repositorio en GitHub](https://github.com/Jerimy2021/Applied-Machine-Learning) · "
    "[wiki del proyecto](https://github.com/Jerimy2021/Applied-Machine-Learning/wiki)"
)
