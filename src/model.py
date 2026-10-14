"""
Pipeline de preprocesamiento, modelos y experimentación para es_incapacitante.

Todo lo que aprende de los datos (imputación, escalado, encoding) vive
dentro de un `Pipeline` de scikit-learn y se ajusta solo con train, nunca
con el dataset completo (ver reports/estrategia_data_preparation.md,
sección 3.6). Los notebooks solo importan y muestran (ver CLAUDE.md).
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import loguniform, norm, randint
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    confusion_matrix,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedGroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

from src.prepare import COLUMNA_NUMERICA, COLUMNAS_CATEGORICAS

RANDOM_STATE = 42

# La clase positiva de negocio es `no incapacitante` (`False`): es la
# minoritaria y la que el README fija como objetivo de recall (sección 2).
CLASE_MINORITARIA = False

SCORING = {
    "recall_minoritaria": make_scorer(recall_score, pos_label=CLASE_MINORITARIA),
    "f1_minoritaria": make_scorer(f1_score, pos_label=CLASE_MINORITARIA),
    "roc_auc": "roc_auc",
}
METRICA_PRINCIPAL = "recall_minoritaria"


def construir_preprocesador() -> ColumnTransformer:
    """
    edad_anios: imputación por mediana + escalado estándar.
    Categóricas: One-Hot, agrupando en `infrequent` las categorías con
    menos de 10 filas (ver estrategia, sección 3.4). Todo dentro de un
    ColumnTransformer que luego va en el mismo Pipeline que el modelo, así
    se ajusta solo con los folds de train de cada partición.
    """
    numerica = Pipeline([
        ("imputar_mediana", SimpleImputer(strategy="median")),
        ("escalar", StandardScaler()),
    ])
    categorica = OneHotEncoder(
        min_frequency=10, handle_unknown="infrequent_if_exist", sparse_output=False
    )
    return ColumnTransformer([
        ("numerica", numerica, [COLUMNA_NUMERICA]),
        ("categorica", categorica, COLUMNAS_CATEGORICAS),
    ])


def construir_cv(n_splits: int = 5) -> StratifiedGroupKFold:
    """Validación cruzada estratificada por `y` y agrupada por evento (estrategia, sección 3.6)."""
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)


def modelos_y_distribuciones() -> dict:
    """
    5 algoritmos de scikit-learn (lineal, basado en distancia, de margen y
    dos de ensamble) con su distribución de hiperparámetros para
    RandomizedSearchCV. `class_weight="balanced"` en los que lo soportan,
    por el desbalance 72.5/27.5 de la población de modelado; KNN no tiene
    ese parámetro, por eso se apoya en la métrica de selección (recall de
    la clase minoritaria) para no favorecer a la mayoritaria.
    """
    return {
        "regresion_logistica": (
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
            {"modelo__C": loguniform(1e-3, 1e2)},
        ),
        "knn": (
            KNeighborsClassifier(),
            {
                "modelo__n_neighbors": randint(3, 31),
                "modelo__weights": ["uniform", "distance"],
                "modelo__p": [1, 2],
            },
        ),
        "svm_rbf": (
            SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=RANDOM_STATE),
            {"modelo__C": loguniform(1e-2, 1e2), "modelo__gamma": loguniform(1e-4, 1e1)},
        ),
        "random_forest": (
            RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE),
            {
                "modelo__n_estimators": randint(150, 900),
                "modelo__max_depth": [None, 4, 8, 12, 16],
                "modelo__min_samples_leaf": randint(1, 10),
                "modelo__max_features": ["sqrt", "log2", None],
            },
        ),
        "gradient_boosting": (
            HistGradientBoostingClassifier(class_weight="balanced", random_state=RANDOM_STATE),
            {
                "modelo__max_iter": randint(80, 350),
                "modelo__learning_rate": loguniform(1e-3, 0.5),
                "modelo__max_depth": [None, 3, 5, 8, 12],
                "modelo__l2_regularization": loguniform(1e-3, 10),
            },
        ),
    }


def buscar_hiperparametros(
    nombre: str,
    modelo,
    distribuciones: dict,
    X: pd.DataFrame,
    y: pd.Series,
    grupos: pd.Series,
    n_iter: int = 40,
) -> RandomizedSearchCV:
    """
    RandomizedSearchCV de un modelo dentro de un Pipeline (preprocesador +
    modelo), con la validación cruzada de `construir_cv()`. Reporta las 3
    métricas de `SCORING`, pero selecciona el mejor modelo por
    `METRICA_PRINCIPAL` (recall de la clase minoritaria).
    """
    pipeline = Pipeline([
        ("preprocesar", construir_preprocesador()),
        ("modelo", modelo),
    ])
    busqueda = RandomizedSearchCV(
        pipeline,
        param_distributions=distribuciones,
        n_iter=n_iter,
        scoring=SCORING,
        refit=METRICA_PRINCIPAL,
        cv=construir_cv(),
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    busqueda.fit(X, y, groups=grupos)
    return busqueda


def comparar_modelos(
    X: pd.DataFrame, y: pd.Series, grupos: pd.Series, n_iter: int = 40
) -> tuple[pd.DataFrame, dict]:
    """
    Corre `buscar_hiperparametros()` para los 5 algoritmos de
    `modelos_y_distribuciones()` y arma una tabla comparativa (una fila
    por modelo, con las 3 métricas promedio de CV en los folds del mejor
    candidato). Devuelve también el diccionario de objetos
    `RandomizedSearchCV` completos, por si se necesita inspeccionar más.
    """
    filas = []
    busquedas = {}
    for nombre, (modelo, distribuciones) in modelos_y_distribuciones().items():
        busqueda = buscar_hiperparametros(
            nombre, modelo, distribuciones, X, y, grupos, n_iter=n_iter
        )
        i = busqueda.best_index_
        resultados = busqueda.cv_results_
        filas.append({
            "modelo": nombre,
            "recall_minoritaria": resultados["mean_test_recall_minoritaria"][i],
            "f1_minoritaria": resultados["mean_test_f1_minoritaria"][i],
            "roc_auc": resultados["mean_test_roc_auc"][i],
            "mejores_parametros": busqueda.best_params_,
        })
        busquedas[nombre] = busqueda
    tabla = pd.DataFrame(filas).sort_values("recall_minoritaria", ascending=False)
    tabla = tabla.reset_index(drop=True)
    return tabla, busquedas


def graficar_comparacion_cv(tabla: pd.DataFrame):
    """Barras agrupadas con las 3 métricas de CV, una barra por modelo."""
    metricas = ["recall_minoritaria", "f1_minoritaria", "roc_auc"]
    x = np.arange(len(tabla))
    ancho = 0.25
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, metrica in enumerate(metricas):
        ax.bar(x + (i - 1) * ancho, tabla[metrica], width=ancho, label=metrica)
    ax.set_xticks(x)
    ax.set_xticklabels(tabla["modelo"], rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Promedio en validación cruzada")
    ax.set_title("Comparación de modelos (validación cruzada, train)")
    ax.legend()
    fig.tight_layout()
    return fig


def refinar_grilla(nombre: str, mejores_parametros: dict) -> dict:
    """
    Grilla exhaustiva acotada alrededor de los mejores hiperparámetros de
    `RandomizedSearchCV`, para afinar con `GridSearchCV` solo el modelo
    ganador (ver estrategia de experimentación acordada: búsqueda aleatoria
    en todos, grilla fina solo en el mejor).
    """
    def _vecinos_log(valor, factor=3, n=3):
        return list(np.geomspace(valor / factor, valor * factor, n))

    def _vecinos_enteros(valor, delta, minimo=1):
        return sorted({max(minimo, valor - delta), valor, valor + delta})

    p = mejores_parametros
    if nombre == "regresion_logistica":
        return {"modelo__C": _vecinos_log(p["modelo__C"])}
    if nombre == "knn":
        return {
            "modelo__n_neighbors": _vecinos_enteros(p["modelo__n_neighbors"], 2, minimo=1),
            "modelo__weights": [p["modelo__weights"]],
            "modelo__p": [p["modelo__p"]],
        }
    if nombre == "svm_rbf":
        return {
            "modelo__C": _vecinos_log(p["modelo__C"]),
            "modelo__gamma": _vecinos_log(p["modelo__gamma"]),
        }
    if nombre == "random_forest":
        return {
            "modelo__n_estimators": _vecinos_enteros(p["modelo__n_estimators"], 150, minimo=50),
            "modelo__max_depth": [p["modelo__max_depth"]],
            "modelo__min_samples_leaf": _vecinos_enteros(
                p["modelo__min_samples_leaf"], 1, minimo=1
            ),
            "modelo__max_features": [p["modelo__max_features"]],
        }
    if nombre == "gradient_boosting":
        return {
            "modelo__max_iter": _vecinos_enteros(p["modelo__max_iter"], 40, minimo=20),
            "modelo__learning_rate": _vecinos_log(p["modelo__learning_rate"]),
            "modelo__max_depth": [p["modelo__max_depth"]],
            "modelo__l2_regularization": _vecinos_log(max(p["modelo__l2_regularization"], 1e-3)),
        }
    raise ValueError(f"Modelo no reconocido: {nombre}")


def afinar_con_grid(nombre: str, modelo, mejores_parametros: dict, X, y, grupos) -> GridSearchCV:
    """
    GridSearchCV sobre `refinar_grilla()`, mismo criterio de selección que
    la búsqueda aleatoria.
    """
    pipeline = Pipeline([
        ("preprocesar", construir_preprocesador()),
        ("modelo", modelo),
    ])
    grilla = GridSearchCV(
        pipeline,
        param_grid=refinar_grilla(nombre, mejores_parametros),
        scoring=SCORING,
        refit=METRICA_PRINCIPAL,
        cv=construir_cv(),
        n_jobs=-1,
    )
    grilla.fit(X, y, groups=grupos)
    return grilla


def intervalo_confianza_proporcion(
    aciertos: int, total: int, confianza: float = 0.95
) -> tuple[float, float]:
    """
    Intervalo de confianza de Wilson para una proporción (ej. recall sobre
    31 casos del test). Más confiable que la aproximación normal cuando
    `total` es chico, como aquí.
    """
    p = aciertos / total
    z = norm.ppf(1 - (1 - confianza) / 2)
    denominador = 1 + z**2 / total
    centro = p + z**2 / (2 * total)
    margen = z * ((p * (1 - p) / total + z**2 / (4 * total**2)) ** 0.5)
    return ((centro - margen) / denominador, (centro + margen) / denominador)


def evaluar_en_test(pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Métricas finales sobre el test (una sola vez). Incluye recall y
    precisión de ambas clases, F1 y AUC-ROC, la matriz de confusión, y el
    intervalo de confianza del 95% del recall minoritario (el test tiene
    solo 31 casos de esa clase, la estimación puntual sola no alcanza).
    """
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, list(pipeline.classes_).index(True)]
    es_minoritaria = y_test == CLASE_MINORITARIA
    aciertos_minoritaria = int(((y_pred == CLASE_MINORITARIA) & es_minoritaria).sum())
    return {
        "recall_minoritaria": recall_score(y_test, y_pred, pos_label=CLASE_MINORITARIA),
        "recall_minoritaria_ic95": intervalo_confianza_proporcion(
            aciertos_minoritaria, int(es_minoritaria.sum())
        ),
        "precision_minoritaria": precision_score(y_test, y_pred, pos_label=CLASE_MINORITARIA),
        "recall_mayoritaria": recall_score(y_test, y_pred, pos_label=True),
        "precision_mayoritaria": precision_score(y_test, y_pred, pos_label=True),
        "f1_minoritaria": f1_score(y_test, y_pred, pos_label=CLASE_MINORITARIA),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "matriz_confusion": confusion_matrix(y_test, y_pred, labels=[False, True]),
    }


def graficar_matriz_confusion(matriz, titulo: str = "Matriz de confusión (test)"):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay(matriz, display_labels=["No incapacitante", "Incapacitante"]).plot(
        ax=ax, colorbar=False
    )
    ax.set_title(titulo)
    fig.tight_layout()
    return fig


def graficar_curvas_roc(modelos_finales: dict, X_test: pd.DataFrame, y_test: pd.Series):
    """Superpone la curva ROC de cada modelo final (uno por nombre) sobre el mismo eje."""
    fig, ax = plt.subplots(figsize=(6, 5))
    for nombre, pipeline in modelos_finales.items():
        RocCurveDisplay.from_estimator(pipeline, X_test, y_test, name=nombre, ax=ax)
    ax.set_title("Curvas ROC en test")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    fig.tight_layout()
    return fig
