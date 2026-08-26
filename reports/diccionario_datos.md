# Diccionario de datos

Este documento registra, para cada columna final del dataset limpio, su
definición y **toda decisión de limpieza aplicada** (imputación, eliminación,
recodificación) junto con su justificación. Ninguna limpieza se aplica en
`src/clean.py` sin quedar documentada aquí primero (ver reglas en CLAUDE.md).

> **Estado:** vacío — pendiente de completar durante la auditoría de
> `data/raw/` en `notebooks/00_inventario_fuentes.ipynb`. Aún no se ha abierto
> ningún `.xlsx` de origen.

## Fuentes crudas (`data/raw/`)

| Archivo | Descripción | Filas | Columnas | Notas |
|---|---|---|---|---|
| `BASE CALCULO INDICADORES 2024.xlsx` | _pendiente de auditar_ | | | |
| `Base Accidentes 2024_Todo Alicorp.xlsx` | _pendiente de auditar_ | | | |
| `Base de Accidentes 2023 _ Total.xlsx` | _pendiente de auditar_ | | | |
| `Resultados SST 2023 v06final.xlsx` | _pendiente de auditar_ | | | |
| `Tablero de Accidentes e incidentes.xlsx` | _pendiente de auditar_ | | | |

## Columnas del dataset limpio

Se completa una fila por columna final (ver estándar de nombres en
`src/schema.py` y en CLAUDE.md — snake_case, sin tildes/ñ, fechas
`datetime64`, categóricas normalizadas en MAYÚSCULAS, booleanas con prefijo
`es_`/`tiene_`).

| Columna | Tipo | Descripción | Valores/categorías válidas | Fuente(s) original(es) |
|---|---|---|---|---|
| _pendiente_ | | | | |

## Nulos detectados

Registrar aquí cada columna con nulos, su cantidad/porcentaje, y la decisión
tomada (nunca imputar silenciosamente — primero reportar y preguntar).

| Columna | # nulos | % nulos | Decisión | Justificación |
|---|---|---|---|---|
| _pendiente_ | | | | |

## Bitácora de decisiones de limpieza

Formato: fecha, columna(s) afectada(s), decisión, justificación, quién decidió.

| Fecha | Columna(s) | Decisión | Justificación | Decidido por |
|---|---|---|---|---|
| _pendiente_ | | | | |

## Anonimización

Registrar aquí qué columnas contienen datos personales (nombres, DNI,
legajos) y qué transformación se les aplicó antes de cualquier salida
compartible (hash / ID sintético).

| Columna original | Transformación aplicada | Método |
|---|---|---|
| _pendiente_ | | |
