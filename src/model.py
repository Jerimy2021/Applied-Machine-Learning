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
from imblearn.over_sampling import SMOTENC
from imblearn.pipeline import Pipeline as PipelineImb
from matplotlib.lines import Line2D
from scipy.stats import loguniform, norm, randint
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
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
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
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


def construir_preprocesador_previo_smote() -> ColumnTransformer:
    """
    Primer paso del pipeline con SMOTENC (ver `construir_pipeline_smote()`):
    imputa `edad_anios` por mediana y codifica las categóricas con
    `OrdinalEncoder` (no son las categorías finales del modelo, solo una
    representación numérica para que SMOTENC pueda generar vecinos
    sintéticos; el One-Hot real va después, en
    `construir_preprocesador_posterior_smote()`). `handle_unknown` con
    valor -1 por si una categoría de test no se vio en train.
    """
    categorica = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    return ColumnTransformer([
        ("numerica", SimpleImputer(strategy="median"), [COLUMNA_NUMERICA]),
        ("categorica", categorica, COLUMNAS_CATEGORICAS),
    ])


def construir_preprocesador_posterior_smote() -> ColumnTransformer:
    """
    Segundo paso del pipeline con SMOTENC: sobre la salida ya remuestreada
    (array posicional: columna 0 = `edad_anios`, columnas 1 en adelante =
    categóricas codificadas), escala la numérica y aplica One-Hot a las
    categóricas (mismo criterio que `construir_preprocesador()`: categorías
    con menos de 10 filas van a `infrequent`).
    """
    indices_categoricas = list(range(1, 1 + len(COLUMNAS_CATEGORICAS)))
    return ColumnTransformer([
        ("escalar", StandardScaler(), [0]),
        ("categorica", OneHotEncoder(
            min_frequency=10, handle_unknown="infrequent_if_exist", sparse_output=False
        ), indices_categoricas),
    ])


def construir_pipeline_smote(modelo, k_neighbors: int = 5) -> PipelineImb:
    """
    Pipeline de `imblearn` (no el de sklearn: este sí soporta un paso que
    cambia el número de filas) con SMOTENC entre el preprocesamiento previo
    y el posterior. SMOTENC, a diferencia de SMOTE, genera vecinos
    sintéticos respetando que `COLUMNAS_CATEGORICAS` son categóricas (usa la
    moda, no interpola, para esas columnas) — necesario porque X mezcla 1
    numérica y 7 categóricas.

    El remuestreo solo ocurre durante `fit` (y solo sobre el fold de train
    de cada partición de `construir_cv()`); `predict`/`predict_proba` no lo
    aplican, igual que cualquier paso de `imblearn.pipeline.Pipeline`. No
    reemplaza datos reales: genera ejemplos minoritarios adicionales solo
    para que el modelo entrene con una clase menos desbalanceada (ver
    reports/estrategia_data_preparation.md, sección "Aumento de datos").
    """
    return PipelineImb([
        ("preprocesar_previo", construir_preprocesador_previo_smote()),
        ("smote", SMOTENC(
            categorical_features=list(range(1, 1 + len(COLUMNAS_CATEGORICAS))),
            k_neighbors=k_neighbors,
            random_state=RANDOM_STATE,
        )),
        ("preprocesar_posterior", construir_preprocesador_posterior_smote()),
        ("modelo", modelo),
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


def evaluar_multisemilla(
    pipeline_base, X: pd.DataFrame, y: pd.Series, grupos: pd.Series, semillas=range(10)
) -> pd.DataFrame:
    """
    Reajusta `pipeline_base` (con los hiperparámetros ya elegidos, sin
    volver a buscarlos) sobre una partición train/test distinta por cada
    semilla, para reportar un rango de recall en vez de un solo número:
    con 564 filas, una sola partición puede ser optimista o pesimista por
    azar. Cada fila de la tabla devuelta es una partición distinta.
    """
    filas = []
    for semilla in semillas:
        cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=semilla)
        idx_train, idx_test = next(cv.split(X, y, groups=grupos))
        modelo = clone(pipeline_base)
        modelo.fit(X.iloc[idx_train], y.iloc[idx_train])
        resultado = evaluar_en_test(modelo, X.iloc[idx_test], y.iloc[idx_test])
        filas.append({
            "semilla": semilla,
            "recall_minoritaria": resultado["recall_minoritaria"],
            "precision_minoritaria": resultado["precision_minoritaria"],
            "f1_minoritaria": resultado["f1_minoritaria"],
            "roc_auc": resultado["roc_auc"],
        })
    return pd.DataFrame(filas)


_ETIQUETAS_MATRIZ = ["No incapacitante", "Incapacitante"]


def _dibujar_matriz_confusion(ax, matriz, titulo: str):
    """
    Dibuja una matriz de confusión en `ax` con el conteo y, debajo, el %
    de esa fila (equivalente al recall de esa clase real): más clara que
    solo el conteo para ver de un vistazo qué tan bien predice cada clase.
    """
    porcentajes_fila = matriz / matriz.sum(axis=1, keepdims=True) * 100
    imagen = ax.imshow(porcentajes_fila, cmap="Blues", vmin=0, vmax=100)
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            color = "white" if porcentajes_fila[i, j] > 60 else "black"
            ax.text(
                j, i, f"{matriz[i, j]}\n{porcentajes_fila[i, j]:.0f}%",
                ha="center", va="center", fontsize=13, color=color,
            )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(_ETIQUETAS_MATRIZ)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(_ETIQUETAS_MATRIZ)
    ax.set_xlabel("Predicho")
    ax.set_ylabel("Real")
    ax.set_title(titulo)
    return imagen


def graficar_matriz_confusion(matriz, titulo: str = "Matriz de confusión (test)"):
    """Matriz de confusión de un modelo, con conteo y % de cada fila (recall de esa clase)."""
    fig, ax = plt.subplots(figsize=(5, 4.3))
    imagen = _dibujar_matriz_confusion(ax, matriz, titulo)
    fig.colorbar(imagen, ax=ax, label="% de la fila (recall de esa clase)")
    fig.tight_layout()
    return fig


def graficar_matrices_confusion_comparadas(resultados: dict):
    """
    Matrices de confusión de varios modelos lado a lado (mismo criterio de
    `graficar_matriz_confusion`), para comparar de un vistazo en una sola
    imagen en vez de una por modelo. `resultados` es el diccionario que
    devuelve `evaluar_en_test()` para cada modelo.
    """
    nombres = list(resultados.keys())
    fig, ejes = plt.subplots(
        1, len(nombres), figsize=(5.6 * len(nombres), 4.3), constrained_layout=True
    )
    ejes = np.atleast_1d(ejes)
    imagen = None
    for ax, nombre in zip(ejes, nombres):
        imagen = _dibujar_matriz_confusion(ax, resultados[nombre]["matriz_confusion"], nombre)
    fig.suptitle("Matrices de confusión en test")
    fig.colorbar(imagen, ax=list(ejes), label="% de la fila (recall de esa clase)", shrink=0.85)
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


def comparar_smote(
    pipeline_base, X: pd.DataFrame, y: pd.Series, grupos: pd.Series,
    modelo, intensidades: tuple = (1.0, 0.75, 0.6, 0.5, 0.4), semillas=range(10),
) -> dict:
    """
    Corre `evaluar_multisemilla()` para el pipeline recomendado (sin
    SMOTENC) y para `construir_pipeline_smote(modelo)` en cada intensidad de
    `intensidades` (1.0 = balance 1:1, el resto = `sampling_strategy` de
    `SMOTENC`, fracción minoritaria/mayoritaria objetivo). Devuelve un
    diccionario {etiqueta: tabla de evaluar_multisemilla}, listo para
    `graficar_comparacion_smote()`.

    Es la verificación del experimento "¿mejora SMOTENC el recall
    objetivo?" (ver reports/estrategia_data_preparation.md, sección
    "Aumento de datos"): compara el mismo modelo final, con y sin SMOTENC,
    sobre las mismas 10 particiones, nunca sobre test combinado con train.
    """
    resultados = {
        "Random Forest (recomendado, sin SMOTENC)": evaluar_multisemilla(
            pipeline_base, X, y, grupos, semillas=semillas
        )
    }
    for intensidad in intensidades:
        sampling_strategy = "auto" if intensidad == 1.0 else intensidad
        pipeline_smote = construir_pipeline_smote(clone(modelo))
        pipeline_smote.named_steps["smote"].set_params(sampling_strategy=sampling_strategy)
        etiqueta = (
            "SMOTENC 1:1" if intensidad == 1.0 else f"SMOTENC (sampling_strategy={intensidad})"
        )
        resultados[etiqueta] = evaluar_multisemilla(
            pipeline_smote, X, y, grupos, semillas=semillas
        )
    return resultados


def graficar_comparacion_recall(resultados_semillas: dict, titulo: str, objetivo: float = 0.70):
    """
    Compara el recall de la clase minoritaria (10 particiones train/test)
    entre varias configuraciones (salida de `evaluar_multisemilla()` por
    configuración, ej. `comparar_smote()`, o un diccionario armado a mano
    con dos tablas). Una fila por configuración: el rango min-max de las
    10 semillas (línea) y la media (punto), contra la línea del objetivo
    del README (recall >= 0.70).

    Verde si las 10 semillas superan el objetivo, rojo si alguna queda por
    debajo: esa es la pregunta que decide si una configuración sirve, no
    el promedio solo (una media alta con una semilla mala igual
    incumpliría el objetivo en la práctica).
    """
    BUENO, MALO = "#0ca30c", "#d03b3b"
    INK, INK_SEC, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

    etiquetas = list(resultados_semillas.keys())
    fig, ax = plt.subplots(figsize=(10, 0.75 * len(etiquetas) + 1.6))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    for i, etiqueta in enumerate(etiquetas):
        serie = resultados_semillas[etiqueta]["recall_minoritaria"]
        minimo, maximo, media = serie.min(), serie.max(), serie.mean()
        n_cumple = int((serie >= objetivo).sum())
        color = BUENO if n_cumple == len(serie) else MALO
        ax.plot([minimo, maximo], [i, i], color=color, linewidth=3,
                solid_capstyle="round", zorder=2)
        ax.scatter([media], [i], color=color, s=150, zorder=3,
                   edgecolor=SURFACE, linewidth=1.5)
        ax.annotate(f"{media:.3f}", (media, i), xytext=(0, 11), textcoords="offset points",
                    ha="center", fontsize=10, color=INK, fontweight="bold")
        ax.annotate(f"{n_cumple}/{len(serie)} semillas ≥ {objetivo:.2f}",
                    (maximo, i), xytext=(12, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=INK_SEC)

    ax.axvline(objetivo, color=MUTED, linestyle="--", linewidth=1.3, zorder=1)
    ax.annotate(
        f"objetivo README: recall ≥ {objetivo:.2f}", xy=(objetivo, -0.75),
        xytext=(6, 0), textcoords="offset points", fontsize=8.5, color=MUTED,
        va="top", ha="left", rotation=90,
    )

    ax.set_yticks(range(len(etiquetas)))
    ax.set_yticklabels(etiquetas, fontsize=10.5, color=INK)
    ax.set_xlabel(
        "Recall de la clase minoritaria (no incapacitante) en 10 particiones de test",
        color=INK_SEC, fontsize=10,
    )
    ax.set_xlim(0.5, 1.02)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED, length=0)
    ax.invert_yaxis()

    handles = [
        Line2D([0], [0], color=BUENO, marker="o", linestyle="-", linewidth=3,
               markersize=9, label="Cumple el objetivo en las 10 semillas"),
        Line2D([0], [0], color=MALO, marker="o", linestyle="-", linewidth=3,
               markersize=9, label="Falla el objetivo en alguna semilla"),
    ]
    leyenda = fig.legend(
        handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.02),
        ncol=2, frameon=False, fontsize=9,
    )
    for texto in leyenda.get_texts():
        texto.set_color(INK_SEC)

    ax.set_title(titulo, fontsize=12.5, color=INK, fontweight="bold", loc="left", pad=16)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    return fig


_EJES_RADAR = ["n_estimators", "max_depth", "min_samples_leaf", "recall_minoritaria"]

# Rango de cada eje para normalizar a [0, 1] en el radar. No es el mínimo/
# máximo observado entre las 3 etapas, es el rango de búsqueda real: el de
# `modelos_y_distribuciones()` para n_estimators/min_samples_leaf, y
# 4-16 (valores posibles de `max_depth` en esa misma búsqueda) extendido a
# 20 para poder ubicar "sin límite" (`None`) sin que quede fuera del eje.
_RANGOS_RADAR_RF = {
    "n_estimators": (150, 1050),
    "max_depth": (4, 20),
    "min_samples_leaf": (1, 10),
    "recall_minoritaria": (0, 1),
}


def graficar_radar_hiperparametros(configuraciones: dict) -> plt.Figure:
    """
    Radar/spider de los hiperparámetros de Random Forest en las etapas de
    búsqueda (ej. RandomizedSearchCV exploratorio -> GridSearchCV afinado
    sobre 2019-2022 -> GridSearchCV final sobre 2019-2022+2024), para
    comparar de un vistazo cuánto se movió cada uno y cómo acompaña el
    recall de la clase minoritaria conseguido en esa etapa.

    `configuraciones`: {etiqueta: {"n_estimators", "max_depth"
    (acepta `None` = sin límite), "min_samples_leaf", "recall_minoritaria"}},
    en el orden en que se quiere dibujar (típicamente de la etapa más
    exploratoria a la final). Las 3 etapas usadas en `04_modelado.ipynb`
    coinciden en `max_features='sqrt'`: por eso no es un eje del radar,
    se anota en el título.

    Cada eje tiene su propio rango real de `_RANGOS_RADAR_RF` (no son
    comparables entre sí): se normalizan solo para poder dibujarlos juntos,
    y el valor real de cada vértice se anota al lado del punto para no
    perder la magnitud original.
    """
    def _normalizar(valor, eje):
        lo, hi = _RANGOS_RADAR_RF[eje]
        v = _RANGOS_RADAR_RF["max_depth"][1] if valor is None else valor
        return (v - lo) / (hi - lo)

    angulos = np.linspace(0, 2 * np.pi, len(_EJES_RADAR), endpoint=False).tolist()
    angulos += angulos[:1]

    INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
    # Claro -> oscuro: misma gama de azul para marcar que es una progresión
    # de etapas de un mismo algoritmo, no modelos distintos a comparar.
    colores = ["#a9cdf0", "#4f93cf", "#0b4f8a", "#062b4a"]

    fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # Las etiquetas de valor se abren en abanico (pequeño corrimiento
    # angular por etapa) en vez de apilarse sobre la misma línea del eje:
    # así, cuando dos etapas caen cerca en valor (ej. min_samples_leaf 8 y
    # 7), el texto no se superpone ni choca con la etiqueta del eje, que
    # vive justo sobre esa línea.
    n_configs = len(configuraciones)
    jitter_angular = 0.065
    # Si dos etapas comparten el mismo valor en un eje (ej. max_depth=12 en
    # exploración y afinado), no se anota dos veces el mismo número: ya
    # queda claro con las dos líneas superpuestas en ese punto; solo se
    # re-anota si el valor cambió respecto a la última etapa vista en ese eje.
    ultimo_valor_por_eje = {}

    for i, ((etiqueta, params), color) in enumerate(zip(configuraciones.items(), colores)):
        valores = [_normalizar(params[eje], eje) for eje in _EJES_RADAR]
        valores += valores[:1]
        ax.plot(angulos, valores, color=color, linewidth=2.2, label=etiqueta, zorder=3)
        ax.fill(angulos, valores, color=color, alpha=0.12, zorder=2)
        for angulo, valor, eje in zip(angulos[:-1], valores[:-1], _EJES_RADAR):
            crudo = params[eje]
            if crudo == ultimo_valor_por_eje.get(eje, object()):
                continue
            ultimo_valor_por_eje[eje] = crudo
            if crudo is None:
                texto = "sin límite"
            elif eje == "recall_minoritaria":
                texto = f"{crudo:.3f}"
            else:
                texto = str(crudo)
            desplazamiento = (i - (n_configs - 1) / 2) * jitter_angular
            ax.text(
                angulo + desplazamiento, valor + 0.07, texto,
                color=color, fontsize=8.5, fontweight="bold",
                ha="center", va="center", zorder=4, clip_on=False,
            )

    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(
        ["n_estimators\n(150-1050)", "max_depth\n(4-20, sin límite=20)",
         "min_samples_leaf\n(1-10)", "recall minoritaria\n(0-1, test u objetivo CV)"],
        fontsize=9, color=INK,
    )
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels([])
    ax.set_ylim(0, 1.18)
    ax.spines["polar"].set_color(MUTED)
    ax.grid(color=GRID)
    ax.tick_params(colors=MUTED)
    ax.set_title(
        "Evolución de hiperparámetros de Random Forest por etapa de búsqueda\n"
        "(max_features = 'sqrt' se mantuvo fijo en todas las etapas)",
        color=INK, fontsize=12, fontweight="bold", pad=22,
    )
    leyenda = fig.legend(
        loc="lower center", bbox_to_anchor=(0.5, -0.03), ncol=1, fontsize=9.5, frameon=False,
    )
    for texto in leyenda.get_texts():
        texto.set_color(INK)
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    return fig
