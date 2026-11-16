"""
Utilidades compartidas por las páginas de la app (Hito 3).

Carga cacheada del pipeline entrenado y de las categorías de X. No
reentrena nada ni depende de `src/` ni de `data/processed/`: la app
queda desacoplada del resto del proyecto, solo lee los artefactos ya
exportados en `models/` (ver `src.model.exportar_pipeline` y
`src.prepare.exportar_categorias_x`, en `notebooks/04_modelado.ipynb`).
"""

import json
from pathlib import Path

import joblib
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"

RECALL_TEST = 0.868
RECALL_IC95 = (0.767, 0.929)

DISCLAIMER = (
    "Esta es una estimación de apoyo a la decisión, con recall de prueba "
    f"{RECALL_TEST:.3f} (IC 95%: {RECALL_IC95[0]:.3f}-{RECALL_IC95[1]:.3f}), "
    "no un resultado certero: no reemplaza la revisión humana de SST "
    "sobre el evento específico."
)


def aplicar_estilos() -> None:
    """
    Inyecta app/estilos.css en la página actual. Se llama al inicio de
    cada página (Inicio.py y cada archivo de pages/), porque Streamlit
    no comparte el `<head>` entre páginas de una app multipágina.
    """
    ruta_css = Path(__file__).resolve().parent / "estilos.css"
    css = ruta_css.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_resource
def cargar_pipeline():
    """
    Carga una sola vez el pipeline final ya entrenado. `st.cache_resource`
    (no `st.cache_data`) porque el objeto cacheado es un estimador vivo de
    scikit-learn, no un dato serializable.
    """
    return joblib.load(MODELS_DIR / "modelo_es_incapacitante.joblib")


@st.cache_data
def cargar_categorias() -> dict:
    """
    Carga una sola vez las categorías de X vistas en train (para poblar
    los desplegables del formulario de predicción). `st.cache_data`
    porque esto sí es un dato plano (el JSON exportado), a diferencia del
    pipeline.
    """
    with open(MODELS_DIR / "categorias_x.json", encoding="utf-8") as f:
        return json.load(f)
