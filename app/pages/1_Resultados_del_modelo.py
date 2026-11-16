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

from common import DISCLAIMER, FIGURES_DIR  # noqa: E402

st.set_page_config(page_title="Resultados del modelo", layout="wide")

st.title("Resultados del modelo (Hito 2)")
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
5 algoritmos de scikit-learn, comparados con `RandomizedSearchCV`
(40 combinaciones, validación cruzada de 5 pliegues agrupada por evento,
solo en train): Regresión Logística, KNN, SVM (RBF), Random Forest y
Gradient Boosting. 4 de los 5 superan el recall de 0.70 que fija el
objetivo del proyecto; KNN queda abajo (no soporta `class_weight`).
"""
    )
    st.image(str(FIGURES_DIR / "modelado_comparacion_cv.png"))

    st.markdown("#### De la validación cruzada al test: por qué gana Random Forest")
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
    st.markdown(
        """
**En palabras simples:** SVM identifica 9 de cada 10 casos leves durante
el entrenamiento, pero en datos nuevos esa cifra cae a solo 8 de 31 (~1
de cada 4): predice casi todo como incapacitante. Random Forest acierta
25 de los mismos 31 casos leves (8 de cada 10), tanto en entrenamiento
como en datos nuevos, por eso es el que se queda.

SVM lideraba la comparación en validación cruzada, pero se desploma en
test: un caso claro de sobreajuste a los pliegues de validación con tan
pocos datos de la clase minoritaria. Random Forest se mantiene estable
entre CV y test.
"""
    )
    col_a, col_b = st.columns(2)
    col_a.image(str(FIGURES_DIR / "modelado_matrices_confusion.png"))
    col_b.image(str(FIGURES_DIR / "modelado_curvas_roc.png"))

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
    st.image(str(FIGURES_DIR / "modelado_radar_hiperparametros.png"))
    st.markdown(
        """
**En palabras simples:** de la etapa 1 a la 2 casi no cambia nada, porque
el afinado solo prueba variantes cercanas al mejor resultado de la
exploración. El salto grande es de la 2 a la 3: con 828 filas en vez de
564 (47% más datos, y mejor balanceadas), el modelo puede permitirse
árboles más profundos y ramas finales más chicas sin memorizar ruido, y
necesita menos árboles para que el voto se estabilice. `max_features='sqrt'`
no cambia en ninguna etapa.

**Validación con varias semillas:** una sola partición train/test puede
ser optimista o pesimista por azar. Reajustando el mismo Random Forest
sobre 10 particiones distintas (2019-2022 solo), el recall va de 0.710 a
0.968 (media 0.813, desviación 0.080): las 10 superan el objetivo, el
modelo no depende de haber tenido suerte con una partición.
"""
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
    st.markdown(
        """
**En palabras simples:** a más balanceo sintético, menos recall, sin
excepciones. El objetivo del proyecto prioriza recall sobre precisión, y
`class_weight="balanced"` ya ataca eso directamente. SMOTENC hace lo
contrario: suaviza la frontera de decisión, lo que mejora precisión y F1
pero vuelve al modelo más conservador para marcar "no incapacitante".
**No se adopta SMOTENC.**
"""
    )

with tab_2024:
    st.markdown(
        """
`accidentes_2024.csv` no tiene `gravedad`, así que se usa como proxy
`dias_dm > 0` de `es_incapacitante`: coincide con la etiqueta real en 458
de 459 filas del histórico 2019-2022, y **SST confirmó que la misma
equivalencia aplica a la fuente 2024**. Con la población combinada (828
filas, mejor balanceada, 59.3%/40.7% frente al 72.5%/27.5% de 2019-2022
solo), Random Forest reafinado da un recall de 0.868 en test (IC 95%:
0.767 a 0.929) y, en 10 semillas, un rango de 0.806 a 0.882 (media 0.852,
desviación 0.025): más alto y más estable que con 2019-2022 solo (media
0.813, desviación 0.080).
"""
    )
    st.image(str(FIGURES_DIR / "modelado_comparacion_2024.png"))
    st.success(
        "Con el proxy ya confirmado por SST, este modelo pasa a ser la "
        "recomendación oficial del Hito 2, en lugar del entrenado solo "
        "con 2019-2022: mismo algoritmo y mismo criterio de selección, "
        "sobre una población más grande y mejor balanceada. Es el modelo "
        "que sirve esta app."
    )

with tab_conclusiones:
    st.markdown(
        """
El objetivo medible del proyecto era clasificar cada evento como
incapacitante/no incapacitante con **recall ≥ 0.70** sobre la clase no
incapacitante. El modelo recomendado lo supera con margen: **recall
0.868 en test** (IC 95%: 0.767-0.929), consistente en 10 particiones
distintas (media 0.852, desviación 0.025).

De los 5 algoritmos comparados, Random Forest ganó no por el mejor score
en validación cruzada (ahí lideraba SVM, 0.880), sino por ser el único
estable entre CV y test. Esa diferencia entre "qué dice la validación
cruzada" y "qué pasa en datos nuevos" es, en retrospectiva, el hallazgo
metodológico más importante del Hito 2.

SMOTENC se evaluó como alternativa para el desbalance de clases y se
descartó con evidencia cuantitativa: empeora el recall de forma monótona
cuanto más balanceo sintético se agrega.
"""
    )
    st.info(
        "**Qué sigue abierto, a propósito:** agrupar `lugar`, "
        "`fuente_peligro` y `puesto_trabajo` (cientos de categorías, "
        "muchas con un solo caso) queda diferido al Hito 3 como trabajo "
        "de *feature engineering*, no es un pendiente de limpieza de este "
        "modelo. Esta app despliega el modelo del Hito 2 sin cambios: el "
        "agrupamiento de categorías no es parte de esta entrega."
    )
    st.markdown(
        """
**Limitaciones:** `experiencia_puesto_meses`, `sexo`,
`area_responsabilidad` y `anio` quedan fuera de X (su disponibilidad
depende de la clase objetivo en el período de entrenamiento). El texto
libre (`descripcion_accidente`) tampoco se usa todavía.
"""
    )
    st.warning(DISCLAIMER)
