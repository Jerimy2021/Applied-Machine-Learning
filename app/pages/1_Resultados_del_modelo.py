"""
Dashboard de resultados del Hito 2 (Visualización y Comunicación, Hito 3).

Reusa el texto y las figuras ya documentadas en README.md sección 9 y en
la wiki (página Modelado): esta página solo las reorganiza en pestañas
para que se puedan escanear en vez de leer de corrido, no reescribe el
contenido. Las figuras se muestran tal cual desde reports/figures/, sin
regenerar nada.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Streamlit no siempre deja en sys.path el directorio del script
# principal (app/) cuando ejecuta una página de pages/ por separado; se
# agrega a mano para no depender de ese detalle de implementación.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import FIGURES_DIR, aplicar_estilos  # noqa: E402

st.set_page_config(page_title="Resultados del modelo", layout="wide")
aplicar_estilos()


def _imagen_centrada(ruta, ancho_relativo: int = 4) -> None:
    """
    Centra una imagen y la acota a un ancho consistente (en vez de
    `use_container_width=True` a secas, que en layout="wide" estira
    imágenes casi cuadradas hasta verse enormes y sin nitidez).
    `ancho_relativo` sobre 6 columnas totales: 4 = la imagen ocupa 4/6
    del ancho, con 1/6 de margen a cada lado.
    """
    margen = (6 - ancho_relativo) / 2
    columnas = st.columns([margen, ancho_relativo, margen])
    with columnas[1]:
        st.image(str(ruta), width="stretch")


st.title("Resultados del modelo")
st.caption(
    "Detalle completo en el "
    "[README](https://github.com/Jerimy2021/Applied-Machine-Learning#9-modelado-hito-2) "
    "y en la [wiki](https://github.com/Jerimy2021/Applied-Machine-Learning/wiki/Modelado)."
)

tab_comparacion, tab_hiperparametros, tab_smotenc, tab_2024, tab_conclusiones = st.tabs(
    [
        "Comparación de algoritmos",
        "Hiperparámetros",
        "SMOTENC",
        "Extensión 2024",
        "Conclusiones finales",
    ]
)

with tab_comparacion:
    st.markdown(
        """
**5 algoritmos comparados** (búsqueda aleatoria de hiperparámetros,
validación cruzada agrupada por evento, solo en train):

- Regresión Logística
- KNN
- SVM (RBF)
- Random Forest
- Gradient Boosting
"""
    )
    st.image(str(FIGURES_DIR / "modelado_comparacion_cv.png"))
    st.caption("4 de los 5 superan el objetivo de recall ≥ 0.70. Solo KNN queda abajo.")

    st.divider()
    st.markdown("#### Pero el ganador no es el que mejor se vio en la comparación")
    st.markdown(
        "Se afinan con más detalle los 2 más prometedores: **SVM**, que lideraba, y "
        "**Random Forest**."
    )
    st.table(
        pd.DataFrame(
            {
                "Modelo": ["SVM (RBF)", "Random Forest"],
                "Recall CV": [0.880, 0.783],
                "Recall test (IC 95%)": ["0.258 (0.14-0.43)", "0.806 (0.64-0.91)"],
                "Precisión test": [1.000, 0.694],
                "F1 test": [0.411, 0.746],
                "AUC-ROC test": [0.792, 0.889],
            }
        ).set_index("Modelo")
    )
    st.caption(
        "SVM identificaba 9 de cada 10 casos leves en el entrenamiento, pero en "
        "datos nuevos esa cifra cae a solo 8 de 31: sobreajuste a los pliegues de "
        "validación. Random Forest se mantiene estable entre CV y test, por eso "
        "es el que se queda."
    )
    # Una debajo de otra, centradas al mismo ancho relativo (no lado a
    # lado): tienen proporciones muy distintas (la de matrices es ancha y
    # baja, la de curvas es casi cuadrada) y forzarlas a la misma columna
    # se veía desparejo.
    _imagen_centrada(FIGURES_DIR / "modelado_matrices_confusion.png")
    _imagen_centrada(FIGURES_DIR / "modelado_curvas_roc.png")

with tab_hiperparametros:
    st.markdown(
        """
Un Random Forest es un conjunto de árboles de decisión que votan la
predicción final. 3 números resumen cómo quedó configurado: cuántos
árboles vota el bosque (`n_estimators`), qué tan profundo puede llegar
cada árbol antes de decidir (`max_depth`) y cuántos casos mínimos
necesita una rama final antes de poder decidir ahí (`min_samples_leaf`).
La búsqueda pasó por 3 etapas, todas optimizando el recall de la clase
minoritaria:
"""
    )
    st.table(
        pd.DataFrame(
            {
                "Etapa": [
                    "1. Exploración (RandomizedSearchCV, 2019-2022)",
                    "2. Afinado (GridSearchCV acotado, 2019-2022)",
                    "3. Final (búsqueda completa + 2024, recomendado)",
                ],
                "n_estimators": [850, 1000, 358],
                "max_depth": [12, 12, 16],
                "min_samples_leaf": [8, 7, 3],
                "Recall": ["0.783 (CV)", "0.806 (test)", "0.868 (test)"],
            }
        ).set_index("Etapa")
    )
    _imagen_centrada(FIGURES_DIR / "modelado_radar_hiperparametros.png", ancho_relativo=4)
    st.caption(
        "De la etapa 1 a la 2 casi no cambia nada: el afinado solo prueba "
        "variantes cercanas al mejor resultado de la exploración. El salto "
        "grande es de la 2 a la 3, con 828 filas en vez de 564: el modelo "
        "puede permitirse árboles más profundos y ramas finales más chicas, "
        "y necesita menos árboles para estabilizar el voto."
    )

    st.divider()
    st.markdown("#### Validación con varias semillas")
    st.markdown(
        "Una sola partición train/test puede ser optimista o pesimista por azar. "
        "Reajustando el mismo Random Forest sobre 10 particiones distintas "
        "(2019-2022 solo), el recall va de 0.710 a 0.968 (media 0.813): las 10 "
        "superan el objetivo."
    )

with tab_smotenc:
    st.markdown(
        """
**¿Qué es SMOTENC?** Genera filas sintéticas de la clase minoritaria
interpolando entre casos reales similares, respetando que la mayoría de
las columnas de X son categóricas (a diferencia del `SMOTE` clásico, que
solo funciona con variables numéricas). Se evaluó como alternativa a
`class_weight="balanced"`, corriendo solo dentro de cada fold de train,
nunca sobre test. No es lo mismo que generar un dataset simulado
completo, que sigue descartado: un accidente inventado no es evidencia
de SST.
"""
    )
    st.table(
        pd.DataFrame(
            {
                "Configuración": [
                    "Random Forest recomendado (sin SMOTENC)",
                    "SMOTENC sampling_strategy=0.4",
                    "SMOTENC sampling_strategy=0.5",
                    "SMOTENC sampling_strategy=0.6",
                    "SMOTENC sampling_strategy=0.75",
                    "SMOTENC 1:1 (balance completo)",
                ],
                "Recall medio (10 semillas)": [0.813, 0.806, 0.768, 0.745, 0.713, 0.690],
                "Recall mínimo": [0.710, 0.677, 0.677, 0.645, 0.613, 0.581],
                "Semillas ≥ 0.70": ["10/10", "9/10", "7/10", "6/10", "5/10", "6/10"],
            }
        ).set_index("Configuración")
    )
    st.image(str(FIGURES_DIR / "modelado_comparacion_smote.png"))
    st.caption(
        "A más balanceo sintético, menos recall, sin excepciones en las 5 "
        "intensidades probadas. No se adopta SMOTENC."
    )

with tab_2024:
    st.markdown(
        "`accidentes_2024.csv` no tiene `gravedad`; se usa un proxy "
        "(`dias_dm > 0`) que **SST confirmó** como equivalente."
    )
    col_recall, col_balance = st.columns(2)
    col_recall.metric(
        "Recall en test",
        "0.868",
        delta="vs. 0.806 solo con 2019-2022",
        help="Población combinada: 828 filas (2019-2022 + 2024)",
    )
    col_balance.metric(
        "Balance de clases (incapacitante / no)",
        "59.3% / 40.7%",
        help="Antes de sumar 2024: 72.5% / 27.5%",
    )
    _imagen_centrada(FIGURES_DIR / "modelado_comparacion_2024.png", ancho_relativo=5)
    st.success(
        "Con el proxy ya confirmado por SST, este modelo pasa a ser la "
        "recomendación oficial del Hito 2: mismo algoritmo y mismo criterio "
        "de selección, sobre una población más grande y mejor balanceada. "
        "Es el modelo que sirve esta app."
    )

with tab_conclusiones:
    _imagen_centrada(FIGURES_DIR / "resumen_objetivo_final.png", ancho_relativo=5)

    st.markdown("#### En 3 ideas")
    st.markdown(
        """
1. **El objetivo se cumplió con margen.** Se pedía recall ≥ 0.70, el
   modelo llega a 0.868.
2. **Ganó por ser confiable, no por el score más alto.** Random Forest
   no lideraba la validación cruzada (SVM sí, con 0.880), pero fue el
   único que se mantuvo estable al pasar a datos nuevos.
3. **SMOTENC se probó y no ayudó.** Más balanceo sintético significó
   siempre menos recall, nunca más.
"""
    )
