# Diccionario de datos

Este documento registra, para cada columna final del dataset limpio, su
definición y **toda decisión de limpieza aplicada** (imputación, eliminación,
recodificación) junto con su justificación. Ninguna limpieza se aplica en
`src/clean.py` / `src/ingest.py` sin quedar documentada aquí (ver reglas en
CLAUDE.md).

> **Estado:** las 5 fuentes de `data/raw/` ya fueron auditadas. 4 de ellas
> tenían (o contenían una hoja con) registros fila-por-accidente/incidente y
> ya están procesadas: `accidentes_2023.csv`, `accidentes_2024.csv`,
> `accidentes_historico_2012_2022.csv` (2012-2022), `accidentes_2025_2026.csv`
> e `incidentes_2025_2026.csv`. Solo `BASE CALCULO INDICADORES 2024.xlsx`
> queda sin procesar: es un archivo de indicadores ya agregados (no fila por
> evento), no aporta registros nuevos para entrenar un modelo.
> Se decidió usar **toda la data limpia disponible** (sin muestrear un % fijo
> por "confidencialidad") porque la confidencialidad ya se resuelve por fila
> con `id_persona` anonimizado — reducir el número de filas no protege más a
> nadie y sí reduce la calidad del futuro modelo.

## Fuentes crudas (`data/raw/`)

| Archivo | Descripción | Filas útiles | Columnas | Notas |
|---|---|---|---|---|
| `Base de Accidentes 2023 _ Total.xlsx` (hoja `Base`) | Registro de accidentes 2023, un accidente por fila | 107 de 306 | 40 | Las 199 filas restantes son residuo de formato de Excel (solo la columna `Sem` traía valor, todo lo demás vacío) — se descartaron en `ingest.load_base_accidentes("2023")`. |
| `Base Accidentes 2024_Todo Alicorp.xlsx` (hoja `Base`) | Registro de accidentes 2024, un accidente por fila | 281 de 281 | 45 (+ 11 columnas `Unnamed` vacías descartadas) | Sin filas de residuo. Incluye 2 columnas booleanas (`Considerar`, `Recategorización`) que las bases 2023 no tienen. |
| `BASE CALCULO INDICADORES 2024.xlsx` | Cálculo de indicadores agregados (hojas `INDICADORES`, `ACCIDENTES`, `HH`, `DÍAS SIN`, `Proyección`) | — | — | No es un registro fila-por-accidente; son tablas de indicadores ya agregados. No se procesó — no aporta filas nuevas para modelar. |
| `Resultados SST 2023 v06final.xlsx` (hoja `HISTORICO ACCIDENTES`) | Tablero histórico multi-año con 42 hojas; la hoja `HISTORICO ACCIDENTES` sí es fila-por-accidente | 1028 (2012-2022) | 27 | Las demás 41 hojas son indicadores/agregados, no auditadas. Se excluyen filas con `anio >= 2023` para no duplicar `accidentes_2023.csv`. |
| `Tablero de Accidentes e incidentes.xlsx` (hoja `2° Accidentes`) | Dashboard; esta hoja es fila-por-accidente, 2025-2026 | 151 | 29 (+ 14 columnas descartadas) | Encabezado real en la fila 2 (`header=1`). Varias columnas de seguimiento (cierre de investigación, difusión de lecciones aprendidas) traían códigos mixtos (`T1`, `T2`, `SI`/`NO` inconsistente) y se descartaron por no poder interpretarlas con confianza — ver bitácora. |
| `Tablero de Accidentes e incidentes.xlsx` (hoja `1° Incidentes`) | Misma dashboard; hoja fila-por-incidente (no accidente), 2025-2026 | 340 | 9 | Hoja distinta a "2° Accidentes": son incidentes (casi-accidentes), no accidentes. No trae nombre/DNI de ninguna persona. |
| `Tablero de Accidentes e incidentes.xlsx` (hojas `TABLERO`, `VISUAL`) | Resto del dashboard | — | — | Vistas/resúmenes visuales del mismo archivo, no registros nuevos. No procesadas. |

## Salida procesada (`data/processed/`)

| Archivo | Filas | Columnas | Generado por |
|---|---|---|---|
| `accidentes_2023.csv` | 107 | 40 | `ingest.load_base_accidentes("2023")` + `ingest.save_processed(...)` |
| `accidentes_2024.csv` | 281 | 45 | `ingest.load_base_accidentes("2024")` + `ingest.save_processed(...)` |
| `accidentes_historico_2012_2022.csv` | 1028 | 27 | `ingest.load_historico_accidentes()` + `ingest.save_processed(...)` |
| `accidentes_2025_2026.csv` | 151 | 29 | `ingest.load_accidentes_tablero()` + `ingest.save_processed(...)` |
| `incidentes_2025_2026.csv` | 340 | 9 | `ingest.load_incidentes()` + `ingest.save_processed(...)` |

**Total de registros de accidentes disponibles: 1567** (107 + 281 + 1028 +
151), más 340 incidentes en un archivo aparte (evento distinto: un incidente
no es un accidente).

Los 5 CSV ya están **anonimizados** (sin nombres/apellidos/DNI, con
`id_persona` donde aplica) y son commiteables según la excepción de
`.gitignore` (ver CONTRIBUTING.md). No se combinaron en un solo archivo
porque sus esquemas no son idénticos entre fuentes (ver columnas exclusivas
por fuente abajo y en `src/schema.py`) — se prefirió mantener trazabilidad
por fuente (columna `fuente_archivo` en todos) antes que forzar un merge que
pudiera perder información. Antes de entrenar un modelo, cada equipo deberá
decidir explícitamente cómo unificar/alinear estos esquemas (ej. quedarse
solo con las columnas comunes, o entrenar por separado).

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

## Columnas de las 3 fuentes adicionales

Esquemas declarados en `src/schema.py` (`ESQUEMA_HISTORICO`,
`ESQUEMA_TABLERO_ACCIDENTES`, `ESQUEMA_INCIDENTES`). Solo se detallan aquí las
columnas que no son evidentes por su nombre o que tuvieron alguna decisión de
limpieza; el resto son análogas a sus contrapartes de `accidentes_2023/2024`.

**`accidentes_historico_2012_2022.csv`** (hoja `HISTORICO ACCIDENTES`):

| Columna | Notas |
|---|---|
| `tipo_contacto` | **100% nula** — esta columna no existía en el Excel para el rango 2012-2022, se introdujo recién en 2023. No es un error, es que el dato no se recolectaba entonces. |
| `gravedad` (`GG`), `dano` (`DAÑO`), `contrata`, `nota_midot`, `modalidad` | Específicas de este archivo, sin equivalente directo en 2023/2024 — no se intentó forzar un mapeo. |
| `fecha_evento` | 85 de 1028 filas (8.3%) quedaron en `NaT`: el texto de fecha en el Excel original tenía errores de tipeo (ej. `"19/012/2018"` con mes inválido, `"08/11/20211"` con un dígito de más en el año, años a 2 dígitos). Se usó `errors="coerce"` — **no se adivinó ninguna fecha**, quedan como `NaT` y deben excluirse de cualquier análisis por fecha. |
| `id_persona` | Igual método que en 2023/2024, hash de la columna `NOMBRE` (que en este archivo viene sola, no separada en apellidos/nombres). |

**`accidentes_2025_2026.csv`** (hoja `2° Accidentes`):

| Columna | Notas |
|---|---|
| `es_hard_stop` | Única columna de seguimiento/checklist de la hoja que se conservó — sus valores eran `SI`/`SÍ`/`NO` limpios. Las demás (cierre de investigación, difusión de lecciones aprendidas, `¿Tiene ROM?`) se descartaron, ver bitácora. |
| `dias_registrables`, `horas_trabajadas_turno`, `tiempo_empresa_meses`/`_anios` | Vienen ya numéricas en el Excel, sin transformación adicional más allá de coerción de tipo. |
| `id_persona` | A diferencia de 2023/2024, aquí la fuente combina apellidos + nombre + **DNI** antes de hashear (el DNI también es PII y se descarta tras usarlo). |

**`incidentes_2025_2026.csv`** (hoja `1° Incidentes`):

| Columna | Notas |
|---|---|
| — | Esta hoja no trae nombre/apellido/DNI de ninguna persona — no requirió anonimización. Es la única de las 5 fuentes procesadas sin columna `id_persona`. |
| `es_verificado` | Booleano `SI`/`NO` del Excel original; 96% nulo (la mayoría de incidentes no tenían este campo llenado). |

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

**`accidentes_historico_2012_2022.csv` (1028 filas):** `tipo_contacto` 100%
nulo (no existía en esa época, ver arriba), `nota_midot` 98.6%, `cargo_ansi`
97.7%, `modalidad` 95.7%, `nro_rom` 90.0%, `contrata` 73.3%,
`area_responsabilidad` 48.7%, `edad_anios` 37.1%.

**`accidentes_2025_2026.csv` (151 filas):** `horas_trabajadas_turno` 98.7%,
`es_hard_stop` 79.5%, `edad_anios` 77.5%, `tiempo_empresa_anios`/`_meses`
~71%, `area` 66.9%, `nro_rom` 55.6%, `hora` 55.0%.

**`incidentes_2025_2026.csv` (340 filas):** `es_verificado` 96.5%,
`danos_reales_o_potenciales` y `fuente_peligro` 72.7% cada una, `empresa` y
`descripcion_incidente` <1% (prácticamente completas).

**Pendiente de decidir con el equipo** (no se decide unilateralmente):
¿qué hacer con las columnas que superan 80% de nulos en cualquiera de los 5
archivos? Opciones a discutir: dejarlas tal cual para el EDA inicial, o
excluirlas de cualquier futuro dataset de modelado por baja cobertura.

## Bitácora de decisiones de limpieza

| Fecha | Columna(s) / filas | Decisión | Justificación | Decidido por |
|---|---|---|---|---|
| 2026-08-28 | Filas 107-305 de `Base de Accidentes 2023 _ Total.xlsx` | Eliminadas | 100% residuo de formato de Excel: solo la columna `Sem` traía valor arrastrado, cero datos reales en el resto de columnas | Claude Code, a pedido del equipo |
| 2026-08-28 | Columnas `Unnamed: 46`-`56` de `Base Accidentes 2024_Todo Alicorp.xlsx` | Eliminadas | Columnas 100% vacías (artefacto de formato de Excel), salvo `Unnamed: 56` con un único valor suelto (`"CONTRATO TEMPORAL"`) que parece un dato mal ubicado — se descartó por no poder atribuirlo con certeza a una fila/columna real | Claude Code, a pedido del equipo |
| 2026-08-28 | `dias_dm_total_indicador` (ambos años) | Coerción a numérico (`errors="coerce"`) | Valores como `"Por confirmar"` no son números; se convierten a `NaN` en vez de inventar un valor | Claude Code, a pedido del equipo |
| 2026-08-28 | `es_recategorizado` (2024) | Blanco → `False` | Es una columna tipo casillero (solo marca `SI` cuando aplica); blanco se interpreta como "no aplica", no como dato faltante | Claude Code, a pedido del equipo |
| 2026-08-28 | `APELLIDO PATERNO`, `APELLIDO MATERNO`, `NOMBRES` (ambos años) | Reemplazadas por `id_persona` (hash) y eliminadas del dataset | Dato personal — ver sección Anonimización | Claude Code, a pedido del equipo |
| 2026-08-30 | Filas con `anio >= 2023` en hoja `HISTORICO ACCIDENTES` | Excluidas de `accidentes_historico_2012_2022.csv` | Ya están cubiertas por `accidentes_2023.csv`/`accidentes_2024.csv`; incluirlas de nuevo duplicaría accidentes | Claude Code, a pedido del equipo |
| 2026-08-30 | `Fecha` de hoja `HISTORICO ACCIDENTES`, 85 filas | Coerción a `NaT` (`errors="coerce"`, `dayfirst=True`) | Texto de fecha mal escrito en el Excel original (mes/año inválido, dígitos de más o de menos) — no se pudo parsear con certeza; se prefirió `NaT` a adivinar la fecha | Claude Code, a pedido del equipo |
| 2026-08-30 | Columnas `¿La Investigación está cerrada?`, `¿Tiene ROM?`, `¿Se difundieron las lecciones aprendidas?`, `¿Se difundió en el espacio diario?`, `T1`/`T1.1`/`T2`/`T2.1`, `DIAS SEGUROS`, columnas `Unnamed` de hoja `2° Accidentes` | Eliminadas | Traían códigos mixtos (contadores numéricos, `T1`/`T2`, `SI`/`NO` inconsistente) o eran artefactos de formato de Excel — no se pudo interpretar su significado con confianza sin preguntarle al equipo que las llena | Claude Code, a pedido del equipo |
| 2026-08-30 | `APELLIDOS DEL ACCIENTADO`, `NOMBRE DEL ACCIDENTADO`, `DNI` de hoja `2° Accidentes` | Reemplazadas por `id_persona` (hash) y eliminadas del dataset | Dato personal (DNI incluido) — ver sección Anonimización | Claude Code, a pedido del equipo |
| 2026-08-30 | Todas las columnas de accidentes/incidentes procesadas | No se aplicó ningún muestreo/recorte de filas por "confidencialidad" | Se confirmó con el equipo que la confidencialidad se resuelve por fila (anonimización de `id_persona`/DNI), no reduciendo la cantidad de filas — reducir filas solo perjudicaría la calidad del futuro modelo sin proteger más a nadie | Decisión del equipo, confirmada explícitamente |

## Anonimización

| Columna original | Transformación aplicada | Método |
|---|---|---|
| `APELLIDO PATERNO` + `APELLIDO MATERNO` + `NOMBRES` (2023/2024) | Reemplazadas por columna nueva `id_persona`; las 3 columnas originales se eliminan del dataset limpio | Hash SHA-256 con salt fijo del proyecto (`clean.anonymize_column`), truncado a 12 caracteres. El mismo trabajador siempre produce el mismo `id_persona`, para poder cruzar sus accidentes sin exponer el nombre. |
| `NOMBRE` (hoja `HISTORICO ACCIDENTES`) | Reemplazada por `id_persona` | Mismo método (hash SHA-256, mismo salt) |
| `APELLIDOS DEL ACCIENTADO` + `NOMBRE DEL ACCIDENTADO` + `DNI` (hoja `2° Accidentes`) | Reemplazadas por `id_persona`; las 3 columnas originales (DNI incluido) se eliminan del dataset limpio | Mismo método (hash SHA-256, mismo salt) |

**Nota:** el salt es el mismo (`"sst-alicorp"`) en las 3 fuentes, por lo que
un mismo trabajador que aparece en más de una fuente con el mismo nombre
producirá el mismo `id_persona` — permite cruzar accidentes de una persona
entre fuentes sin exponer su identidad. La hoja `1° Incidentes` no tiene
`id_persona` porque no trae ningún dato de identidad de personas.

**⚠️ Pendiente de revisión:** `descripcion_accidente` (en las 3 fuentes que la
tienen: 2023, 2024 y `accidentes_2025_2026.csv`) y `descripcion_incidente` /
`danos_reales_o_potenciales` (en `incidentes_2025_2026.csv`) son texto libre
escrito por la persona que reportó el evento. No se aplicó ninguna
anonimización sobre estos campos — es posible que algunas descripciones
mencionen nombres de personas dentro del texto. **Antes de compartir estos
campos fuera del equipo** (ej. en una presentación, un notebook exportado a PDF, etc.), alguien
debe revisar manualmente una muestra o correr una limpieza de texto adicional.
No se resolvió en esta pasada por el tiempo que toma hacerlo bien.
