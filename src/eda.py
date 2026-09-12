"""
Funciones reutilizables de EDA dirigido a la variable objetivo
`es_incapacitante` (ver reports/diccionario_datos.md, sección "Variable
objetivo"). Los notebooks solo importan y muestran estos resultados, no
implementan la lógica (ver CLAUDE.md).
"""

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


def cramers_v(x: pd.Series, y: pd.Series) -> float:
    """
    Coeficiente V de Cramér entre dos columnas categóricas: mide asociación
    entre 0 (ninguna) y 1 (perfecta) — el equivalente a una correlación de
    Pearson pero para variables categóricas, donde Pearson no aplica.

    Las filas con nulo en `x` o en `y` se excluyen del cálculo (no se
    imputan).
    """
    datos = pd.DataFrame({"x": x, "y": y}).dropna()
    tabla = pd.crosstab(datos["x"], datos["y"])
    chi2 = chi2_contingency(tabla)[0]
    n = tabla.to_numpy().sum()
    k, r = tabla.shape
    return float(np.sqrt((chi2 / n) / (min(k, r) - 1)))


def tasa_incapacitante_por_categoria(columna: pd.Series, y: pd.Series) -> pd.DataFrame:
    """
    Tabla de contingencia simple: para cada valor de `columna`, cuántos
    casos hay (`n`) y qué porcentaje de ellos es incapacitante
    (`pct_incapacitante`, sobre `y == True`).

    Las filas con nulo en `columna` o en `y` se excluyen del cálculo (no se
    imputan). Ordenado por `n` descendente.
    """
    datos = pd.DataFrame({"categoria": columna, "es_incapacitante": y}).dropna()
    resumen = datos.groupby("categoria", observed=True)["es_incapacitante"].agg(
        n="count", pct_incapacitante="mean"
    )
    resumen["pct_incapacitante"] = (resumen["pct_incapacitante"] * 100).round(2)
    return resumen.sort_values("n", ascending=False)
