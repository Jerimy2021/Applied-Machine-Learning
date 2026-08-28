# Diccionario de datos

Este documento registra, para cada columna final del dataset limpio, su
definición y **toda decisión de limpieza aplicada** (imputación, eliminación,
recodificación) junto con su justificación. Ninguna limpieza se aplica en
`src/clean.py` / `src/ingest.py` sin quedar documentada aquí (ver reglas en
CLAUDE.md).

> **Estado:** primera pasada completa sobre las 2 fuentes con registros
> fila-por-accidente (2023 y 2024). Las otras 3 fuentes son tableros/
> indicadores agregados — quedan pendientes de una decisión de si aportan
> algo distinto a nivel fila (ver tabla de fuentes).

## Fuentes crudas (`data/raw/`)

| Archivo | Descripción | Filas útiles | Columnas | Notas |
|---|---|---|---|---|
| `Base de Accidentes 2023 _ Total.xlsx` (hoja `Base`) | Registro de accidentes 2023, un accidente por fila | 107 de 306 | 40 | Las 199 filas restantes son residuo de formato de Excel (solo la columna `Sem` traía valor, todo lo demás vacío) — se descartaron en `ingest.load_base_accidentes("2023")`. |
| `Base Accidentes 2024_Todo Alicorp.xlsx` (hoja `Base`) | Registro de accidentes 2024, un accidente por fila | 281 de 281 | 45 (+ 11 columnas `Unnamed` vacías descartadas) | Sin filas de residuo. Incluye 2 columnas booleanas (`Considerar`, `Recategorización`) que las bases 2023 no tienen. |
| `BASE CALCULO INDICADORES 2024.xlsx` | Cálculo de indicadores agregados (hojas `INDICADORES`, `ACCIDENTES`, `HH`, `DÍAS SIN`, `Proyección`) | — | — | No es un registro fila-por-accidente; son tablas de indicadores ya agregados. Pendiente decidir si se usa para EDA de indicadores. |
| `Resultados SST 2023 v06final.xlsx` | Tablero histórico multi-año con 42 hojas (indicadores, horas-hombre, capacitaciones, etc.) | — | — | Tablero muy heterogéneo, no auditado a fondo todavía. No se usó en esta pasada. |
| `Tablero de Accidentes e incidentes.xlsx` | Dashboard con hojas `1° Incidentes`, `2° Accidentes`, `TABLERO`, `VISUAL` | — | — | Parece ser una vista/resumen de las mismas bases de accidentes. No auditado a fondo — revisar si duplica info de las 2 bases ya procesadas antes de usarlo. |

## Salida procesada (`data/processed/`)

| Archivo | Filas | Columnas | Generado por |
|---|---|---|---|
| `accidentes_2023.csv` | 107 | 40 | `ingest.load_base_accidentes("2023")` + `ingest.save_processed(...)` |
| `accidentes_2024.csv` | 281 | 45 | `ingest.load_base_accidentes("2024")` + `ingest.save_processed(...)` |

Ambos ya están **anonimizados** (sin nombres/apellidos, con `id_persona`) y
son commiteables según la excepción de `.gitignore` (ver CONTRIBUTING.md).
No se combinaron en un solo archivo porque sus esquemas no son idénticos
(ver columnas exclusivas por año abajo) — se prefirió mantener trazabilidad
por fuente antes que forzar un merge que pudiera perder información.

## Columnas del dataset limpio

Común a ambos años salvo que se indique lo contrario. Fechas parseadas con
`errors="coerce"`: un valor no parseable queda `NaN`, no se inventa.

| Columna | Tipo | Descripción | Notas |
|---|---|---|---|
| `item` | float | Número de item/correlativo del registro original | Muchos nulos en 2023 (93%) — el Excel original no lo llenaba consistentemente |
| `nro_rom` | str | Código interno de registro (ej. `ITD23107`) | No es dato personal, es un código de trámite interno |
| `pais` | category | País de la sede | |
| `sociedad` | category | Razón social | |
| `predio` | category | Predio/sede física | |
| `planta` | category | Planta | |
| `planta_sigma` | category | Código de planta (sistema Sigma) | Solo 2024 |
| `direccion` | category | Dirección de responsabilidad/área gerencial | |
| `area` | category | Área donde ocurrió el evento | |
| `tipo_accidente`, `tipo_accidente_2`, `tipo_accidente_3` | category | Clasificación del tipo de accidente | Solo 2024 |
| `fecha_evento` | datetime64 | Fecha del accidente | |
| `semana`, `dia`, `mes`, `anio` | float | Descomposición de la fecha, tal como venía en el Excel | Redundante con `fecha_evento`; se mantiene por si el Excel original tenía inconsistencias entre ambos |
| `hora` | object (`datetime.time`) | Hora del accidente | |
| `turno` | category | Turno de trabajo | |
| `tipo_trabajador` | category | Tipo de trabajador (propio/tercero, etc.) | |
| `empresa` | category | Empresa del trabajador | |
| `sexo` | category | Sexo del trabajador | |
| `edad_anios` | float | Edad del trabajador | |
| `puesto_trabajo` | category | Puesto de trabajo | |
| `fecha_ingreso_labores` | datetime64 | Fecha de ingreso del trabajador | Muchos nulos (~43-90%) |
| `descripcion_accidente` | str (texto libre) | Descripción narrativa del accidente | **Ver advertencia de confidencialidad abajo** |
| `tipo_contacto` | category | Tipo de contacto/mecanismo del accidente | |
| `parte_cuerpo_afectada`, `parte_cuerpo_afectada_2` | category | Parte del cuerpo afectada | |
| `actividad_realizada` | category | Actividad que se realizaba | |
| `proceso` | category | Proceso productivo | Solo 2023 |
| `diagnostico_medico` | category | Diagnóstico médico | |
| `lesion` | category | Tipo de lesión | |
| `dias_dm` | float | Días de descanso médico | |
| `cargo_ansi` | category | Clasificación de cargo según norma ANSI | |
| `dias_dm_total_indicador` | float | Días de DM para el indicador oficial | Valores como `"Por confirmar"` se convirtieron a `NaN` (no se inventó un número) |
| `situacion_actual` | category | Situación actual del caso | |
| `tiempo_experiencia_meses` | float | Experiencia del trabajador en meses | |
| `puesto` | category | Puesto (columna adicional a `puesto_trabajo`) | Solo 2023 |
| `antiguedad` | category | Antigüedad del trabajador | |
| `fuente_peligro` | category | Fuente de peligro | |
| `tipo_contrato` | category | Tipo de contrato | |
| `poblacion` | float | Población/dotación asociada | Solo 2024 |
| `es_considerado` | boolean | Si el caso se considera para el indicador oficial | Solo 2024. Nulo cuando el Excel no lo especificaba (no se asumió ni Sí ni No) |
| `es_recategorizado` | bool | Si el caso fue recategorizado | Solo 2024. **Decisión:** el Excel original solo marcaba `SI` cuando aplicaba y dejaba en blanco el resto — se asumió blanco = `False` (no recategorizado), no `NaN`, porque es una columna tipo casillero/flag, no un dato que falte reportar |
| `id_persona` | str | Hash SHA-256 (12 car.) de apellido paterno + apellido materno + nombres | Ver sección Anonimización |
| `fuente_archivo` | str | `"2023"` o `"2024"`, para trazabilidad | |

## Nulos detectados

**No se imputó ningún nulo en esta pasada** — quedan como `NaN`/`NaT` en
`data/processed/`. Resumen de las columnas con más nulos (ver
`clean.report_nulls(df)` para el detalle completo por archivo):

**`accidentes_2023.csv` (107 filas):**

| Columna | % nulos | Decisión |
|---|---|---|
| `item` | 93% | Sin decisión aún — probablemente no útil como feature, evaluar en EDA |
| `nro_rom` | 92% | Sin decisión aún |
| `fecha_ingreso_labores` | 90% | Sin decisión aún |
| `tiempo_experiencia_meses`, `parte_cuerpo_afectada`, `actividad_realizada`, `dia`/`mes`/`anio`, `puesto`, `situacion_actual` | 84% | El Excel original solo llenaba estos campos para un subconjunto de registros — pendiente entender el criterio antes de decidir imputar/eliminar/dejar como está |
| `cargo_ansi` | 83% | Pendiente |
| `tipo_contrato` | 71% | Pendiente |

**`accidentes_2024.csv` (281 filas):** nulos mucho más moderados (la mayoría
de columnas bajo 10%); las más altas son `es_considerado` (69%, columna que
el Excel original solo llena a veces) y `fecha_ingreso_labores` (43%).

**Pendiente de decidir con el equipo** (no se decide unilateralmente):
¿qué hacer con las columnas de `accidentes_2023.csv` que superan 80% de
nulos? Opciones a discutir: dejarlas tal cual para el EDA inicial, o
excluirlas de cualquier futuro dataset de modelado por baja cobertura.

## Bitácora de decisiones de limpieza

| Fecha | Columna(s) / filas | Decisión | Justificación | Decidido por |
|---|---|---|---|---|
| 2026-08-28 | Filas 107-305 de `Base de Accidentes 2023 _ Total.xlsx` | Eliminadas | 100% residuo de formato de Excel: solo la columna `Sem` traía valor arrastrado, cero datos reales en el resto de columnas | Claude Code, a pedido del equipo |
| 2026-08-28 | Columnas `Unnamed: 46`-`56` de `Base Accidentes 2024_Todo Alicorp.xlsx` | Eliminadas | Columnas 100% vacías (artefacto de formato de Excel), salvo `Unnamed: 56` con un único valor suelto (`"CONTRATO TEMPORAL"`) que parece un dato mal ubicado — se descartó por no poder atribuirlo con certeza a una fila/columna real | Claude Code, a pedido del equipo |
| 2026-08-28 | `dias_dm_total_indicador` (ambos años) | Coerción a numérico (`errors="coerce"`) | Valores como `"Por confirmar"` no son números; se convierten a `NaN` en vez de inventar un valor | Claude Code, a pedido del equipo |
| 2026-08-28 | `es_recategorizado` (2024) | Blanco → `False` | Es una columna tipo casillero (solo marca `SI` cuando aplica); blanco se interpreta como "no aplica", no como dato faltante | Claude Code, a pedido del equipo |
| 2026-08-28 | `APELLIDO PATERNO`, `APELLIDO MATERNO`, `NOMBRES` (ambos años) | Reemplazadas por `id_persona` (hash) y eliminadas del dataset | Dato personal — ver sección Anonimización | Claude Code, a pedido del equipo |

## Anonimización

| Columna original | Transformación aplicada | Método |
|---|---|---|
| `APELLIDO PATERNO` + `APELLIDO MATERNO` + `NOMBRES` (concatenados) | Reemplazadas por columna nueva `id_persona`; las 3 columnas originales se eliminan del dataset limpio | Hash SHA-256 con salt fijo del proyecto (`clean.anonymize_column`), truncado a 12 caracteres. El mismo trabajador siempre produce el mismo `id_persona`, para poder cruzar sus accidentes sin exponer el nombre. |

**⚠️ Pendiente de revisión:** `descripcion_accidente` es texto libre escrito
por la persona que reportó el accidente. No se aplicó ninguna anonimización
sobre este campo — es posible que algunas descripciones mencionen nombres
de personas dentro del texto. **Antes de compartir este campo fuera del
equipo** (ej. en una presentación, un notebook exportado a PDF, etc.), alguien
debe revisar manualmente una muestra o correr una limpieza de texto adicional.
No se resolvió en esta pasada por el tiempo que toma hacerlo bien.
