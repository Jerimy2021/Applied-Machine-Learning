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

# Numero grande primero (lo que mas importa), dentro de una tarjeta con
# degradado y animacion de entrada. El "antes/ahora" va como una sola
# linea de 2 etiquetas, no 2 bloques de texto, para que se lea de un
# vistazo en vez de leerse como un parrafo mas.
st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-stat">
            <div class="hero-stat-numero">{RECALL_TEST:.1%}</div>
            <div class="hero-stat-etiqueta">
                de los accidentes <strong>no incapacitantes</strong> se identifican
                correctamente (recall en test)
            </div>
        </div>
        <div class="antes-ahora">
            <span class="etiqueta antes">Antes: criterio del supervisor</span>
            <span class="flecha">&rarr;</span>
            <span class="etiqueta ahora">Ahora: modelo entrenado con 828 casos reales</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
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
