"""
Limpieza y normalización de la data de accidentes/incidentes SST.

Funciones reutilizables de limpieza (renombrado de columnas al estándar
snake_case, normalización de categóricas, parseo de fechas, etc.).

Toda decisión de limpieza (imputación, eliminación, recodificación) debe
quedar registrada con su justificación en reports/diccionario_datos.md antes
de aplicarse aquí. Prohibido imputar silenciosamente: report_nulls() solo
reporta, nunca rellena — la decisión de qué hacer con cada nulo se toma y
documenta primero, y se implementa después como un paso explícito.
"""

import hashlib
import re
import unicodedata

import numpy as np
import pandas as pd


def report_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reporta nulos por columna (cantidad y % sobre el total de filas).

    No imputa nada. Usar el resultado para llenar la sección "Nulos
    detectados" de reports/diccionario_datos.md y decidir ahí qué hacer con
    cada columna antes de escribir la función de limpieza correspondiente.
    """
    n_nulos = df.isna().sum()
    pct_nulos = (n_nulos / len(df) * 100).round(2)
    reporte = pd.DataFrame({"n_nulos": n_nulos, "pct_nulos": pct_nulos})
    return reporte[reporte["n_nulos"] > 0].sort_values("n_nulos", ascending=False)


def report_outliers_iqr(df: pd.DataFrame, columnas: list[str] | None = None) -> pd.DataFrame:
    """
    Reporta valores atípicos (outliers) por columna numérica, con la regla
    del rango intercuartílico (IQR): un valor es atípico si cae fuera de
    [Q1 - 1.5*IQR, Q3 + 1.5*IQR].

    No elimina ni capa nada — mismo principio que report_nulls(): primero se
    reporta, la decisión de qué hacer con cada outlier (dejarlo, caparlo,
    revisarlo caso a caso) se toma después y se documenta en
    reports/diccionario_datos.md.

    columnas: columnas a evaluar; por defecto, todas las numéricas del
    DataFrame.
    """
    if columnas is None:
        columnas = df.select_dtypes(include="number").columns.tolist()

    filas = []
    for col in columnas:
        serie = df[col].dropna()
        if serie.empty:
            continue
        q1, q3 = serie.quantile([0.25, 0.75])
        iqr = q3 - q1
        limite_inf, limite_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        atipicos = serie[(serie < limite_inf) | (serie > limite_sup)]
        filas.append({
            "columna": col,
            "n_outliers": len(atipicos),
            "pct_outliers": round(len(atipicos) / len(serie) * 100, 2),
            "limite_inferior": round(float(limite_inf), 2),
            "limite_superior": round(float(limite_sup), 2),
            "min": serie.min(),
            "max": serie.max(),
        })
    if not filas:
        return pd.DataFrame(
            columns=["n_outliers", "pct_outliers", "limite_inferior", "limite_superior",
                     "min", "max"]
        )
    reporte = pd.DataFrame(filas).set_index("columna")
    return reporte[reporte["n_outliers"] > 0].sort_values("n_outliers", ascending=False)


def anonymize_column(df: pd.DataFrame, column: str, salt: str = "") -> pd.DataFrame:
    """
    Reemplaza los valores de una columna sensible (nombres, DNI, legajos) por
    un ID sintético (hash SHA-256 truncado a 12 caracteres). El mismo valor
    original siempre produce el mismo ID, para poder seguir cruzando tablas
    sin exponer el dato real.

    No modifica el DataFrame recibido: devuelve una copia.

    Documentar en reports/diccionario_datos.md (sección "Anonimización") cada
    columna a la que se le aplica esta función.
    """
    def _hash(valor):
        if pd.isna(valor):
            return valor  # un nulo sigue siendo nulo, no se "anonimiza" a un hash
        return hashlib.sha256((salt + str(valor)).encode("utf-8")).hexdigest()[:12]

    df = df.copy()
    df[column] = df[column].apply(_hash)
    return df


def strip_accents(texto: str) -> str:
    """Quita tildes/diacríticos de un texto (ej. 'Área' -> 'Area')."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def normalize_categorical(serie: pd.Series) -> pd.Series:
    """
    Normaliza una columna categórica al estándar de CLAUDE.md: sin espacios
    sobrantes, MAYÚSCULAS, sin tildes, dtype 'category'. Un string vacío
    tras el strip se trata como nulo (no como una categoría propia).
    """
    limpio = (
        serie.astype("string")
        .str.strip()
        .apply(lambda v: strip_accents(v).upper() if pd.notna(v) else v)
    )
    limpio = limpio.replace("", pd.NA)
    return limpio.astype("category")


_PATRON_ID_ETIQUETADO = re.compile(r"\b(DNI|RUC)\b[\s:.\-]*\d{6,11}", re.IGNORECASE)

_MAY = "A-ZÁÉÍÓÚÑÜ"
_MIN = "a-záéíóúñü"
_TITULOS = r"Sr|Sra|Srta|Ing|Dr|Dra"

# Secuencia de 2 a 6 palabras en Título-Caso (candidato a nombre propio, ej.
# "Ysmael Pinares Vargas"). Se extendió de 2-4 a 2-6 palabras: se encontró un
# nombre real de 5 palabras ("Pedro Phil Renato Bocanegra Colacci") que el
# límite anterior cortaba, dejando el último apellido sin enmascarar (ver
# revisión humana del 2026-09-17 en reports/diccionario_datos.md).
_PATRON_NOMBRE_PROPIO = re.compile(rf"\b[{_MAY}][{_MIN}]+(?:\s+[{_MAY}][{_MIN}]+){{1,5}}\b")

# Título (Sr./Sra./Srta./Ing./Dr./Dra.) + nombre de una sola palabra, con
# abreviatura opcional (ej. "Sr. Freddy C.") — cubre nombres que el patrón de
# arriba no agarra por tener un único término en Título-Caso.
_PATRON_TITULO_NOMBRE = re.compile(rf"\b({_TITULOS})\.\s+([{_MAY}][{_MIN}]+(?:\s+[{_MAY}]\.)?)")

# "colaborador/compañero/trabajador/operario <Nombre> [SIGLA]" — la palabra
# de rol es un indicador fuerte de que sigue un nombre propio, incluso si es
# una sola palabra o trae una sigla en MAYÚSCULAS pegada (ej. "Pacaya CA").
# El lookahead negativo evita interpretar un título como si fuera el nombre
# (ej. "compañero Sr. Urrutia" lo resuelve el patrón de título de arriba).
_PATRON_ROL_NOMBRE = re.compile(
    rf"\b(colaborador|colaboradora|compañero|compañera|trabajador|trabajadora|"
    rf"operario|operaria)\s+(?!(?:{_TITULOS})\.)([{_MAY}][{_MIN}]+(?:\s+[A-ZÑÜ]{{2,4}}\b)?)"
)

# "<Nombre> (Accidentado)" — el paréntesis rotula explícitamente que la
# palabra previa es el nombre de la persona afectada.
_PATRON_ACCIDENTADO = re.compile(rf"\b([{_MAY}][{_MIN}]+)(?=\s*\([Aa]ccidentad[oa]\))")


def redact_pii_libre(serie: pd.Series) -> pd.Series:
    """
    Enmascara, en una columna de texto libre (ej. `descripcion_accidente`),
    lo que probablemente es un dato personal:
      - DNI/RUC etiquetados explícitamente (ej. "DNI 09065660") -> "[DNI]"/"[RUC]"
      - Secuencias de 2 a 6 palabras en Título-Caso (candidato a nombre
        propio, ej. "Ysmael Pinares Vargas") -> "[NOMBRE]"
      - Título (Sr./Sra./Srta./Ing./Dr./Dra.) + nombre de una sola palabra
        (ej. "Sr. Muñoz") -> "Sr. [NOMBRE]"
      - "colaborador/compañero/trabajador/operario <Nombre>" (ej.
        "el colaborador Carlos") -> "el colaborador [NOMBRE]"
      - "<Nombre> (Accidentado)" (ej. "Denis (Accidentado)") -> "[NOMBRE] (Accidentado)"
      - Cualquier palabra de un nombre ya identificado en la misma fila que
        vuelva a aparecer suelta más adelante (ej. se menciona a la misma
        persona solo por su nombre o apellido en una oración posterior).

    **Es una heurística de primera pasada, no un NER validado** (ver
    reports/diccionario_datos.md, secciones "Incidente de PII" y "Revisión
    humana de texto redactado (2026-09-17)"):
      - Puede enmascarar nombres de lugar/clínica/empresa que también están
        en Título-Caso (falso positivo, ej. "Molino Santa Rosa", "Supervisor
        de Turno Oscar Orrego" → sobre-enmascara "Turno"). Se prioriza no
        dejar pasar un nombre de persona sobre preservar esos términos.
      - Apellidos con conector en minúscula (ej. "David de la Cruz") solo
        enmascaran la primera palabra ("David"), el conector rompe la
        secuencia de Título-Caso — limitación conocida, no resuelta.
      - No reconoce nombres en minúsculas ni patrones fuera de los cubiertos
        arriba (ej. una sola palabra sin título ni contexto de rol).
    No reemplaza una revisión humana antes de compartir esta columna fuera
    del equipo.
    """
    def _enmascarar(valor):
        if pd.isna(valor):
            return valor
        texto = _PATRON_ID_ETIQUETADO.sub(lambda m: f"[{m.group(1).upper()}]", str(valor))

        nombres_hallados = set()

        def _base(m):
            nombres_hallados.update(m.group(0).split())
            return "[NOMBRE]"

        def _titulo(m):
            nombres_hallados.update(m.group(2).split())
            return f"{m.group(1)}. [NOMBRE]"

        def _rol(m):
            nombres_hallados.update(m.group(2).split())
            return f"{m.group(1)} [NOMBRE]"

        def _accidentado(m):
            nombres_hallados.add(m.group(1))
            return "[NOMBRE]"

        # El patrón base (multi-palabra) va primero: si "trabajador"/"Sr."
        # van seguidos de un nombre de 2+ palabras, debe ganarlo el patrón
        # base completo, no el de rol/título (que solo captura 1 palabra) —
        # si corrieran antes, dejarían la segunda palabra del nombre suelta.
        texto = _PATRON_NOMBRE_PROPIO.sub(_base, texto)
        texto = _PATRON_TITULO_NOMBRE.sub(_titulo, texto)
        texto = _PATRON_ROL_NOMBRE.sub(_rol, texto)
        texto = _PATRON_ACCIDENTADO.sub(_accidentado, texto)

        # Segunda pasada: si una palabra de un nombre ya identificado en
        # esta misma fila vuelve a aparecer suelta más adelante en el mismo
        # texto, también se enmascara — evita fugas por menciones repetidas
        # de una persona ya identificada (ej. "David Chilca" ... "el Sr.
        # David" más adelante, mismo texto).
        for palabra in sorted(nombres_hallados, key=len, reverse=True):
            if len(palabra) < 2 or not re.match(rf"^[{_MAY}]", palabra):
                continue
            texto = re.sub(rf"\b{re.escape(palabra)}\b", "[NOMBRE]", texto)

        return texto

    return serie.apply(_enmascarar)


_MAPA_TURNO = {
    # Sinónimos de turno numerado (mismo esquema, distinta redacción).
    "1RO": "TURNO_1", "1": "TURNO_1", "1ERO": "TURNO_1", "1ER": "TURNO_1",
    "1ER TURNO": "TURNO_1",
    "2DO": "TURNO_2", "2": "TURNO_2", "2NDO": "TURNO_2", "2DO TURNO": "TURNO_2",
    "2RO": "TURNO_2",
    "3RO": "TURNO_3", "3": "TURNO_3", "3ER": "TURNO_3",
    # Sinónimos dentro de la misma franja horaria (no del esquema numerado).
    "MANANA": "DIA",
    "MADRUGADA": "NOCHE", "MEDIA NOCHE": "NOCHE",
    # Marcador de "no reportado", mismo criterio que en sexo/gravedad.
    "-": pd.NA,
}


def normalize_turno(serie: pd.Series) -> pd.Series:
    """
    Agrupa los sinónimos de la columna `turno` de
    `accidentes_historico_2012_2022.csv` en 6 categorías finales: `TURNO_1`,
    `TURNO_2`, `TURNO_3` (turno numerado — ej. "1RO"/"1ER"/"1ER TURNO" son la
    misma cosa escrita distinto) y `DIA`, `TARDE`, `NOCHE` (franja horaria —
    "MANANA" se une a `DIA`; "MADRUGADA"/"MEDIA NOCHE" se unen a `NOCHE`).

    **Decisión explícita del equipo**: NO se asume que un turno numerado
    corresponda a una franja horaria (ej. turno 1 = DIA) — sería inventar una
    equivalencia de negocio no verificable con la data disponible, así que
    ambos esquemas quedan como categorías separadas. `"-"` se trata como
    nulo (mismo criterio que en `sexo`/`gravedad`). Ver
    reports/diccionario_datos.md.

    Espera una serie ya pasada por `normalize_categorical` (mayúsculas, sin
    tildes). Cualquier valor no reconocido en el mapeo (incluido `NaN`) se
    deja tal cual, no se descarta silenciosamente.
    """
    limpio = serie.astype("string").map(
        lambda v: _MAPA_TURNO.get(v, v) if pd.notna(v) else v
    )
    return limpio.astype("category")


_UNIDAD_A_MESES = {
    # Años: variantes reales observadas en experiencia_puesto (incluye un
    # typo real, "NOS" = "años" sin la "a" inicial, ej. "1.5 ños").
    "ANOS": 12, "ANO": 12, "AANOS": 12, "NOS": 12,
    "MESES": 1, "MES": 1, "MESE": 1,  # MESE: typo real ("2 mese", "7 mese")
    "DIAS": 1 / 30, "DIA": 1 / 30, "DIAW": 1 / 30,  # DIAW: typo real ("7 DIAW")
    "SEMANAS": 7 / 30, "SEMANA": 7 / 30,
}
_ALT_UNIDADES = "|".join(sorted(_UNIDAD_A_MESES, key=len, reverse=True))
_PATRON_CANTIDAD_UNIDAD = re.compile(
    rf"(\d+(?:[.,]\d+)?)\s*({_ALT_UNIDADES})\b(\s*Y\s*MEDIO)?"
)
_PATRON_SOLO_NUMERO = re.compile(r"^\d+(?:[.,]\d+)?$")


def parse_experiencia_puesto(serie: pd.Series) -> pd.Series:
    """
    Parsea la columna `experiencia_puesto` (texto libre, ej. "7 años y 10
    meses", "3 AÑOS", "1.5 ños") a una nueva columna numérica en meses
    (float64). Convierte años (x12), meses (x1), semanas y días (aprox.
    1 mes = 30 días, conversión estándar documentada, no un dato inventado).

    Reglas para no adivinar (si no se puede verificar el valor exacto, queda
    en `pd.NA`, no se estima):
      - `"-"` / vacío -> `NA` (mismo criterio que el resto del proyecto).
      - Un número suelto sin unidad (ej. `"228"`) -> `NA`: no se puede saber
        si son días, meses o años.
      - Texto con comparación ("MENOS DE 1 AÑO", "MAYOR 15 AÑOS") -> `NA`:
        no es un valor puntual, es un rango sin límite verificable.
      - Texto con `"/"` o salto de línea (varios valores concatenados, ej.
        "1 SEMANA / 3 AÑOS" o dos periodos en labores distintas) -> `NA`: no
        hay forma de saber cuál es el valor correcto o si deben sumarse.
      - Si después de extraer los números con unidad reconocida sobra texto
        sin explicar (ej. un typo no reconocible como `"7eses"`, o texto de
        otra columna pegado por error como `"LIMPEZA TÉCNICA"`) -> `NA`: no
        se descarta el resto del texto silenciosamente, se prefiere no
        convertir la fila entera.
      - Texto entre paréntesis o después de `" EN "` (ej. "2 años en el
        puesto (3 años y 2 meses en Alicorp)", "4 meses en Alicorp") se
        ignora: se toma solo la cifra principal, antes de esa aclaración.

    Verificado contra los 692 valores no nulos de
    `accidentes_historico_2012_2022.csv`: 644 se convierten (93.1%), 48
    quedan en `NA` (38 son `"-"`, el resto son los casos ambiguos de arriba,
    cada uno revisado a mano) — ver bitácora en reports/diccionario_datos.md.
    """
    def _parsear(valor):
        if pd.isna(valor):
            return np.nan
        texto = strip_accents(str(valor)).upper().replace("\xa0", " ")
        texto = re.sub(r"\s+", " ", texto).strip()
        if texto in ("", "-"):
            return np.nan
        if _PATRON_SOLO_NUMERO.match(texto):
            return np.nan
        if "MENOS DE" in texto or "MAYOR" in texto:
            return np.nan
        if "/" in texto or "\n" in texto:
            return np.nan
        texto = re.sub(r"\bUNA?\b", "1", texto)
        texto = texto.split("(")[0].split(" EN ")[0].strip()

        total = 0.0
        resto = texto
        encontrado = False
        for m in _PATRON_CANTIDAD_UNIDAD.finditer(texto):
            cantidad = float(m.group(1).replace(",", "."))
            valor_meses = cantidad * _UNIDAD_A_MESES[m.group(2)]
            if m.group(3):  # "... Y MEDIO"
                valor_meses += 0.5 * _UNIDAD_A_MESES[m.group(2)]
            total += valor_meses
            encontrado = True
            resto = resto.replace(m.group(0), " ", 1)

        if not encontrado:
            return np.nan

        # Lo que sobra tras quitar los matches debe ser solo "Y"/puntuación;
        # si queda texto sin explicar, no se adivina y se descarta la fila.
        resto_limpio = re.sub(r"\bY\b|[.,]|\s+", "", resto)
        if resto_limpio != "":
            return np.nan

        return round(total, 2)

    return serie.apply(_parsear).astype("float64")


def derive_es_incapacitante(gravedad: pd.Series) -> pd.Series:
    """
    Deriva la etiqueta booleana `es_incapacitante` a partir de la columna
    `gravedad` de `accidentes_historico_2012_2022.csv` (única fuente que la
    trae). Reglas acordadas con el equipo (ver reports/diccionario_datos.md,
    sección "Variable objetivo"):

      - Contiene "INCAPACITANTE" sin "NO " inmediatamente antes -> True
      - Contiene "NO INCAPACITANTE" -> False
      - Contiene "INCIDENTE" (incluida la variante mal escrita "INCICENTE")
        -> False
      - Cualquier otro valor (incl. "-", nulo, y los 2 casos pendientes de
        revisión caso a caso "ACCIDENTE FUERA DEL TRABAJO" y
        "DAÑO A LA SALUD") -> `pd.NA`. No se imputa ni se adivina.

    Espera `gravedad` ya normalizada por `normalize_categorical` (mayúsculas,
    sin tildes) — igual funciona si no lo está, salvo por tildes.
    """
    def _clasificar(valor):
        if pd.isna(valor):
            return pd.NA
        # Colapsa espacios múltiples (el dato original trae, ej., "DANO   A LA SULUD").
        texto = " ".join(str(valor).split())
        if "NO INCAPACITANTE" in texto:
            return False
        if "INCAPACITANTE" in texto:
            return True
        if "INCIDENTE" in texto or "INCICENTE" in texto:
            return False
        return pd.NA

    return gravedad.apply(_clasificar).astype("boolean")
