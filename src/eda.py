"""
Funciones reutilizables de EDA dirigido a la variable objetivo
`es_incapacitante` (ver reports/diccionario_datos.md, sección "Variable
objetivo"). Los notebooks solo importan y muestran estos resultados, no
implementan la lógica (ver CLAUDE.md).
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
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


def describe_numeric(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """
    Estadística descriptiva de columnas numéricas: n, % de nulos, media,
    desviación, mínimo, percentiles 5/25/50/75/95, máximo y asimetría
    (skew > 0: cola larga hacia valores altos). Los nulos se excluyen del
    cálculo, no se imputan.
    """
    filas = {}
    for col in columnas:
        serie = df[col].dropna()
        p5, p25, p50, p75, p95 = serie.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
        filas[col] = {
            "n": len(serie),
            "pct_nulos": round(df[col].isna().mean() * 100, 1),
            "media": serie.mean(),
            "desviacion": serie.std(),
            "min": serie.min(),
            "p5": p5,
            "p25": p25,
            "mediana": p50,
            "p75": p75,
            "p95": p95,
            "max": serie.max(),
            "asimetria": serie.skew(),
        }
    return pd.DataFrame(filas).T.round(2)


def describe_categorical(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """
    Resumen de columnas categóricas: % de nulos, número de categorías,
    categoría dominante con su % (sobre los no nulos) y cuántas categorías
    aparecen una sola vez (indicador de cardinalidad fragmentada).
    """
    filas = {}
    for col in columnas:
        conteo = df[col].value_counts()
        n_validos = df[col].notna().sum()
        filas[col] = {
            "pct_nulos": round(df[col].isna().mean() * 100, 1),
            "n_categorias": len(conteo),
            "categoria_dominante": conteo.index[0],
            "pct_dominante": round(conteo.iloc[0] / n_validos * 100, 1),
            "categorias_con_1_caso": int((conteo == 1).sum()),
        }
    return pd.DataFrame(filas).T


def nulos_por_anio(df: pd.DataFrame, columnas: list[str], col_anio: str = "anio") -> pd.DataFrame:
    """% de nulos de cada columna, por año (filas = año). Solo reporta, no imputa."""
    return df.groupby(col_anio)[columnas].agg(lambda s: s.isna().mean() * 100).round(0)


def plot_histogramas(df: pd.DataFrame, columnas: list[str], recortar_p95: tuple = ()):
    """
    Histogramas de columnas numéricas. Las columnas en `recortar_p95` se
    grafican solo hasta su percentil 95 (el título indica cuántos valores
    quedan fuera) para que una cola extrema no aplaste el resto; los datos
    no se modifican.
    """
    fig, axes = plt.subplots(1, len(columnas), figsize=(4.5 * len(columnas), 3.6))
    for ax, col in zip(np.atleast_1d(axes), columnas):
        serie = df[col].dropna()
        titulo = col
        if col in recortar_p95:
            tope = serie.quantile(0.95)
            titulo = f"{col} (hasta p95={tope:.0f}; {int((serie > tope).sum())} fuera)"
            serie = serie[serie <= tope]
        if serie.nunique() <= 15:
            serie.value_counts().sort_index().plot(kind="bar", ax=ax)
        else:
            ax.hist(serie, bins=25)
        ax.set_title(titulo, fontsize=10)
        ax.set_ylabel("n filas")
    fig.tight_layout()
    return fig


def plot_barras_categoricas(df: pd.DataFrame, columnas: list[str], top: int = 10, ncols: int = 3):
    """Barras horizontales de las `top` categorías más frecuentes de cada columna."""
    nrows = -(-len(columnas) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.4 * nrows))
    axes = np.atleast_1d(axes).ravel()
    for ax, col in zip(axes, columnas):
        conteo = df[col].value_counts().head(top).sort_values()
        conteo.plot(kind="barh", ax=ax)
        n_cat = df[col].nunique()
        ax.set_title(f"{col} (top {min(top, n_cat)} de {n_cat})", fontsize=10)
        ax.set_ylabel("")
        ax.tick_params(axis="y", labelsize=8)
    for ax in axes[len(columnas):]:
        ax.set_visible(False)
    fig.tight_layout()
    return fig


def plot_nulos(df: pd.DataFrame, umbral: float = 80):
    """% de nulos por columna (solo las que tienen alguno), con línea en `umbral`%."""
    pct = (df.isna().mean() * 100).sort_values()
    pct = pct[pct > 0]
    fig, ax = plt.subplots(figsize=(7, 0.32 * len(pct) + 1))
    pct.plot(kind="barh", ax=ax)
    ax.axvline(umbral, color="red", linestyle="--", linewidth=1)
    ax.set_xlabel("% de nulos")
    ax.set_title("Valores faltantes por columna")
    fig.tight_layout()
    return fig


def plot_nulos_por_anio(tabla: pd.DataFrame):
    """Mapa de calor del % de nulos por año (salida de `nulos_por_anio`)."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    sns.heatmap(tabla, annot=True, fmt=".0f", cmap="Reds", vmin=0, vmax=100, ax=ax,
                cbar_kws={"label": "% de nulos"})
    ax.set_title("% de nulos por año (histórico 2012-2022)")
    ax.set_ylabel("año")
    fig.tight_layout()
    return fig
