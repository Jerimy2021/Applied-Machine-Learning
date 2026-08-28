# Flujo de trabajo: limpieza de datos y EDA

Guía para el equipo sobre cómo limpiar la data y hacer el EDA de forma
consistente con las reglas de `CLAUDE.md`. Léela antes de tocar `data/` o
escribir en `src/`.

## Principios (no negociables — vienen de `CLAUDE.md`)

1. **`data/raw/` es solo lectura.** Ningún script ni notebook escribe ahí.
2. **`data/` no se commitea**, con una única excepción: los `.csv` finales y
   **anonimizados** dentro de `data/processed/` (ver sección de `.gitignore`
   más abajo). `data/raw/` y `data/interim/` nunca se commitean, en ningún
   formato.
3. **Prohibido imputar silenciosamente.** Si una columna tiene nulos, primero
   se reporta (`clean.report_nulls`) y se documenta la decisión en
   `reports/diccionario_datos.md` — recién después se implementa.
4. **Toda decisión de limpieza** (imputación, eliminación, recodificación)
   se registra en `reports/diccionario_datos.md` con su justificación.
5. **Anonimizar antes de compartir.** Nombres, DNI y legajos se reemplazan
   por un ID sintético (`clean.anonymize_column`) antes de cualquier salida
   que salga del entorno de trabajo (commit, notebook exportado, print en
   una reunión).
6. **Los notebooks solo importan y muestran.** La lógica reutilizable (carga,
   limpieza, validación de esquema) vive en `src/`.

## Excepción de `.gitignore` para CSV

```gitignore
data/*
!data/processed/
data/processed/*
!data/processed/*.csv
```

Esto significa: **solo** los `.csv` que estén directamente en
`data/processed/` pueden commitearse. Cualquier otra cosa en `data/`
(incluyendo `.xlsx`/`.xls` en cualquier carpeta, y **todo** lo que esté en
`data/raw/` o `data/interim/`) sigue ignorado. Antes de hacer
`git add data/processed/algo.csv`, confirmar los tres puntos del checklist
al final de este documento.

## Flujo de limpieza de datos (paso a paso)

1. **Auditar la fuente** en `notebooks/00_inventario_fuentes.ipynb`: hojas,
   columnas, tipos, dimensiones de cada archivo de `data/raw/`.
2. **Cargar** con `ingest.load_raw("nombre_del_archivo.xlsx")` — no usar
   `pd.read_excel` directo en el notebook, así toda carga queda centralizada
   y reutilizable.
3. **Reportar, no imputar:** correr `clean.report_nulls(df)` y revisar
   también duplicados/inconsistencias (categorías mal escritas, tipos
   mezclados, fechas fuera de rango). Nada se corrige todavía en este paso.
4. **Documentar el hallazgo** en `reports/diccionario_datos.md`
   (`Nulos detectados` / `Bitácora de decisiones de limpieza`) proponiendo
   qué hacer con cada caso (imputar con qué criterio, eliminar filas,
   recodificar) y por qué.
5. **Validar con el equipo** (PR o standup) antes de aplicar una decisión que
   no sea obvia — sobre todo si implica eliminar filas o imputar valores.
6. **Implementar** la limpieza aprobada como función pura en `src/clean.py`
   (recibe el DataFrame crudo, devuelve el DataFrame limpio; no debe leer ni
   escribir archivos). Nombrar columnas en snake_case, sin tildes/ñ,
   categóricas en MAYÚSCULAS, fechas como `datetime64` (`fecha_evento`),
   booleanas con prefijo `es_`/`tiene_` — y declarar cada una en
   `src/schema.py`.
7. **Anonimizar** las columnas con datos personales con
   `clean.anonymize_column(df, "columna")`. Documentar el método en
   `reports/diccionario_datos.md` (sección `Anonimización`).
8. **Guardar:**
   - Resultados parciales/de trabajo → `ingest.save_interim(df, "nombre")`
     (nunca se commitea, úsalo libremente).
   - Resultado final, ya limpio y anonimizado →
     `ingest.save_processed(df, "nombre")` (este sí se puede commitear).

## Flujo de EDA (paso a paso)

1. Partir siempre de `data/processed/` (nunca leer `data/raw/` directo desde
   el notebook de EDA — si falta algo, se agrega en el flujo de limpieza).
2. En `notebooks/01_eda_accidentes.ipynb`: importar desde `src/`, no
   reimplementar lógica de carga/limpieza ahí.
3. Vista general: `df.shape`, `df.dtypes`, `df.describe()`.
4. Univariado: distribución de las variables clave (fecha, tipo de evento,
   área, gravedad, parte del cuerpo afectada, días perdidos).
5. Bivariado / temporal: accidentes por mes, por área, cruces tipo × gravedad,
   tendencia en el tiempo.
6. Guardar cada figura relevante en `reports/figures/` con nombre
   descriptivo (ej. `accidentes_por_mes_2023.png`).
7. Anotar los hallazgos como texto markdown en el propio notebook; si cambian
   el entendimiento de alguna columna, reflejarlo también en
   `reports/diccionario_datos.md`.
8. **Antes de compartir el notebook fuera del equipo:** revisar que ninguna
   celda de salida (tablas, prints, gráficos) muestre nombres, DNI o legajos
   sin anonimizar.

## Checklist antes de un PR que agrega/modifica un CSV

- [ ] El `.csv` vive en `data/processed/` (no en `raw/` ni `interim/`)
- [ ] Pasó por `clean.anonymize_column()` en toda columna con datos personales
- [ ] Sus columnas están documentadas en `reports/diccionario_datos.md` y
      declaradas en `src/schema.py`
- [ ] `git ls-files data/` solo muestra `.csv` de `data/processed/` — nada de
      `data/raw/`, `data/interim/`, ni `.xlsx`/`.xls`

Este checklist también está en `.github/pull_request_template.md`.
