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
| `id_persona` | Igual método que en 2023/2024, hash de la columna `NOMBRE` (que en este archivo viene sola, no separada en apellidos/nombres). 54 filas (5.25%) quedan nulas: el Excel original no traía nombre en esas filas. |
| `programa` | Categórica, sede/programa productivo (ej. `GALLETERA LIMA`, `COPSA`, `TEAL`, `BOLIVIA`, `DETERGENTES`). 20.7% nula. |
| `lugar` | Categórica, sede física donde ocurrió el evento (ej. `COPSA`, `GALLETERA LIMA`, `NUTRICION ANIMAL TRUJILLO`). Distinta de `area_responsabilidad`. 6.0% nula. |
| `experiencia_puesto` | Texto libre (`object`), sin transformación: mezcla formatos como `"7 años y 10 meses"`, `"3 años"`. **Calidad de dato**: al menos un valor observado (`"Accidente Incapacitante "`) no es una experiencia sino texto de otra columna, aparentemente mal ubicado en el Excel original — no se corrigió, se reporta tal cual. |
| `dias_perdidos` | Numérica, días de descanso médico por la lesión. 11.1% nula. Análoga a `dias_dm` de 2023/2024. |
| `dias_mas_ansi` | Numérica, días adicionales según cargo ANSI. 11.2% nula. Análoga a `dias_dm_total_indicador` de 2023/2024. |

**`accidentes_2025_2026.csv`** (hoja `2° Accidentes`):

| Columna | Notas |
|---|---|
| `es_hard_stop` | Única columna de seguimiento/checklist de la hoja que se conservó — sus valores eran `SI`/`SÍ`/`NO` limpios. Las demás (cierre de investigación, difusión de lecciones aprendidas, `¿Tiene ROM?`) se descartaron, ver bitácora. |
| `dias_registrables`, `horas_trabajadas_turno`, `tiempo_empresa_meses`/`_anios` | Vienen ya numéricas en el Excel, sin transformación adicional más allá de coerción de tipo. |
| `id_persona` | A diferencia de 2023/2024, aquí la fuente combina apellidos + nombre + **DNI** antes de hashear (el DNI también es PII y se descarta tras usarlo). |
| `vicepresidencia` | Categórica (`SUPPLY CHAIN`, `OTRAS VICEPRESIDENCIAS`, `ADMINISTRACION`). 0.7% nula. |
| `categoria` | Categórica, línea de negocio/dirección (ej. `HOME Y PERSONAL CARE`, `FARINACEOS`, `MOLINOS`). Sin nulos. |
| `dia_semana` | Categórica, día de la semana del evento (`LUNES`...`DOMINGO`), redundante con `fecha_evento`. Sin nulos. |
| `causa_basica`, `causa_principal` | Categóricas según metodología SCAT; texto largo y con variantes de redacción muy similares (ej. dos versiones de "ESTANDARES DE TRABAJO INADECUADOS..." que difieren solo en un espacio) — no se unificaron, quedan como categorías distintas. 49.0% y 3.3% nulas respectivamente. |
| `causa_inmediata` | Categórica: `ACTO INSEGURO` / `CONDICION INSEGURA`. 3.3% nula. |
| `trimestre` | Categórica (`T1`-`T4`), redundante con `fecha_evento`. Sin nulos. |

**`incidentes_2025_2026.csv`** (hoja `1° Incidentes`):

| Columna | Notas |
|---|---|
| — | Esta hoja no trae nombre/apellido/DNI de ninguna persona — no requirió anonimización. Es la única de las 5 fuentes procesadas sin columna `id_persona`. |
| `tipo_evento` | Categórica: mayoría `INCIDENTE` (201), `ALTO POTENCIAL` (82), `DANO MATERIAL` (44); el resto son ~10 categorías con 1-2 casos cada una (ej. `FUGA DE CLORO`, `AMAGO DE INCENDIO`), incluyendo una variante mal escrita (`INDICENTE`, 1 caso) no unificada con `INCIDENTE`. Sin nulos. |
| `es_verificado` | Booleano `SI`/`NO` del Excel original; 96% nulo (la mayoría de incidentes no tenían este campo llenado). |

## Variable objetivo: `es_incapacitante`

Booleana (`boolean` nullable), derivada de `gravedad` en
`accidentes_historico_2012_2022.csv` por `clean.derive_es_incapacitante()`
(única fuente con `gravedad`; las demás 4 fuentes no tienen esta columna, por
lo tanto no aportan y para este target). Reglas acordadas con el equipo:

| Regla sobre `gravedad` | Resultado |
|---|---|
| Contiene "INCAPACITANTE" sin "NO " inmediatamente antes | `True` |
| Contiene "NO INCAPACITANTE" | `False` |
| Contiene "INCIDENTE" (incl. variante mal escrita "INCICENTE") | `False` |
| Cualquier otro valor: `"-"`, nulo, "ACCIDENTE FUERA DEL TRABAJO", "DAÑO A LA SALUD" | `pd.NA` — no se imputa ni se adivina |

**Decisión confirmada (2026-09-12):** los 2 casos "ACCIDENTE FUERA DEL
TRABAJO" y "DAÑO A LA SALUD" se quedan en `pd.NA` (excluidos de
entrenamiento/evaluación) — no se reclasifican a `True`/`False` ni se
eliminan las filas del dataset. Ya no es un pendiente, es el comportamiento
final de `derive_es_incapacitante()`.

Resultado sobre las 1028 filas: 861 `True`, 155 `False`, 12 `<NA>`
(verificado corriendo la función). Las filas con `<NA>` deben excluirse de
entrenamiento/evaluación, no imputarse. Sobre las 1016 filas con etiqueta
definida (excluyendo los 12 `<NA>`): **861 `True` (84.74%) / 155 `False`
(15.26%)** — el desbalance ~85/15 a tratar explícitamente en el modelo.

**Por qué no se usó `gravedad` cruda ni `dias_perdidos > 0` como target:**
`gravedad` tiene 15 categorías (varias con 0-4 casos y errores de tipeo,
ver arriba) — no es entrenable así. `dias_perdidos > 0` da un desbalance
peor (93.3% / 6.7% sobre las filas no nulas) y además tiene 11.1% de nulos.

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
`area_responsabilidad` 48.7%, `edad_anios` 37.45% (incluye 4 valores
imposibles corregidos a `NaN`, ver sección "Valores atípicos"),
`dias_perdidos` 11.38% y `dias_mas_ansi` 11.58% (ídem, incluyen valores en
6000 corregidos).

**`accidentes_2025_2026.csv` (151 filas):** `horas_trabajadas_turno` 98.7%,
`es_hard_stop` 79.5%, `edad_anios` 77.5%, `tiempo_empresa_anios`/`_meses`
~71%, `area` 66.9%, `nro_rom` 55.6%, `hora` 55.0%.

**`incidentes_2025_2026.csv` (340 filas):** `es_verificado` 96.5%,
`danos_reales_o_potenciales` y `fuente_peligro` 72.7% cada una, `empresa` y
`descripcion_incidente` <1% (prácticamente completas).

## Valores atípicos (outliers)

**Misma política que con los nulos: no se elimina ni se capa ningún outlier
silenciosamente.** Se detectan con la regla del rango intercuartílico (IQR:
atípico si cae fuera de `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]`, vía
`clean.report_outliers_iqr()`) y se visualizan con boxplot en
`01_eda_accidentes.ipynb` (`reports/figures/outliers_boxplot_*.png`). Qué
hacer con cada uno (dejarlo, caparlo, investigarlo caso a caso) queda
pendiente de decisión del equipo — no se decidió en esta pasada.

**Hallazgos concretos (verificados corriendo el reporte, sin corregir nada):**

| Archivo | Columna | Outliers (IQR) | Mín / Máx | Nota |
|---|---|---|---|---|
| `accidentes_2023.csv` + `accidentes_2024.csv` | `dias_dm` | 38 de 352 (10.8%) | 0 / 180 | — |
| ídem | `dias_dm_total_indicador` | 36 de 329 (10.9%) | 0 / 904 | — |
| ídem | `tiempo_experiencia_meses` | 24 de 194 (12.4%), **2 corregidas** | 0 / 2190→`NaN` | Ya corregido (ver decisión abajo) |
| `accidentes_historico_2012_2022.csv` | `dias_perdidos` | 110 de 914 (12.0%), **3 corregidas** | 0 / 6000→`NaN` | Ya corregido |
| ídem | `dias_mas_ansi` | 111 de 913 (12.2%), **4 corregidas** | 0 / 6000→`NaN` | Ya corregido — 1 fila más de lo reportado antes (fila con `dias_perdidos=0` pero `dias_mas_ansi=6000`, encontrada al verificar ambas columnas juntas) |
| ídem | `nota_midot` | 3 de 14 (21.4%) | 28 / 75 | Muestra muy chica (14 no nulos de 1028) — sin corregir, no hay regla de negocio clara para esta columna |
| ídem | **`edad_anios`** | 0 (no marcado por IQR), **4 corregidas** | 0→`NaN` / 63 | Ya corregido (ver decisión abajo) |
| `accidentes_2025_2026.csv` | `dias_registrables` | 18 de 151 (11.9%) | 1 / 1140 | Sin corregir — 1140 días (~3 años) es extremo pero no hay una regla de negocio verificable (a diferencia de `edad_anios`/`tiempo_experiencia_meses`) que lo marque como imposible |
| ídem | `tiempo_empresa_meses` / `tiempo_empresa_anios` | 1 cada una | — | Sin corregir, mismo motivo |

**Decisión tomada (2026-09-12):** se corrigen a `NA` (sin imputar ningún
reemplazo) solo los valores que violan una **regla de negocio verificable**,
no todo lo que el IQR marca como estadísticamente atípico — un valor
extremo no es automáticamente un error:

- `edad_anios <= 0` en `accidentes_historico_2012_2022.csv` (4 filas): una
  edad de 0 es imposible para un trabajador.
- `tiempo_experiencia_meses / 12 > edad_anios` en `accidentes_2024.csv`
  (2 filas, ninguna en 2023): nadie puede tener más años de experiencia que
  de vida — regla relativa a la propia fila, no un umbral fijo.
- `dias_perdidos == 6000` y `dias_mas_ansi == 6000` en
  `accidentes_historico_2012_2022.csv` (4 filas en total, no 3: se encontró
  una fila adicional con `dias_perdidos=0` pero `dias_mas_ansi=6000`,
  inconsistente entre sí): el mismo valor exacto repetido en filas de
  accidentes distintos y no relacionados es más compatible con un
  tope/placeholder del sistema de origen que con un dato real — no se
  intentó adivinar el valor real, se marca como `NA`.

**Se decide explícitamente NO tocar** el resto de los outliers IQR de la
tabla (`dias_dm`, `dias_dm_total_indicador`, `nota_midot`,
`dias_registrables`, `tiempo_empresa_meses/anios`): son estadísticamente
extremos pero no violan ninguna regla de negocio verificable con la
información disponible — capar o eliminar un valor solo por ser grande
sería inventar un criterio, no corregir un error confirmado. Implementado en
`src/ingest.py` (`load_base_accidentes`, `load_historico_accidentes`).

**Decisión tomada (2026-09-12):** las columnas con >80% de nulos en
cualquiera de los 5 archivos (`item`, `nro_rom`, `cargo_ansi`,
`tipo_contacto`, `nota_midot`, `modalidad`, `horas_trabajadas_turno`,
`es_verificado`, etc.) **se quedan en `data/processed/` sin eliminar** — en
esta fase de EDA/limpieza no se restringe el dataset. Quedan marcadas aquí
como "no recomendadas como X por baja cobertura"; la decisión de excluirlas
o no de un dataset de modelado se toma en la fase de modelado, con el
contexto de ese momento (ver README, sección 5, para las X ya descartadas
del target actual por este mismo motivo).

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
| 2026-09-12 | `turno` (fila 920) y `experiencia_puesto` (filas 12 y 36) de `HISTORICO ACCIDENTES` | Celda puesta en `NA`, resto de la fila conservado | Las 3 celdas traían el mismo texto que `GG` (gravedad) de su propia fila (ej. `"Accidente Incapacitante"`) — una celda mal pegada, no un valor propio de esa columna. Se verificó fila por fila que **no** es un corrimiento de columnas: el resto de cada fila (fecha, parte del cuerpo, año, mes, días perdidos, fuente de peligro, actividad) tiene valores normales para su propia columna. Se corrige solo la celda puntual, no se toca nada más de la fila | Equipo, confirmado con inspección fila por fila |
| 2026-09-12 | `turno` de `HISTORICO ACCIDENTES` | Sinónimos agrupados con `clean.normalize_turno()`: `1RO`/`1`/`1ERO`/`1ER`/`1ER TURNO`→`TURNO_1`; `2DO`/`2`/`2NDO`/`2DO TURNO`/`2RO`→`TURNO_2`; `3RO`/`3`/`3ER`→`TURNO_3`; `MANANA`→`DIA`; `MADRUGADA`/`MEDIA NOCHE`→`NOCHE`. `DIA`/`TARDE`/`NOCHE` sin cambio | De 21 categorías (20 valores + `NaN`) a 7 (`TURNO_1`, `TURNO_2`, `TURNO_3`, `DIA`, `TARDE`, `NOCHE`, `NaN`). **No se unificó** el esquema numerado con el de franja horaria (ej. no se asumió turno 1 = DIA) porque sería inventar una equivalencia de negocio no verificable | Equipo, aprobado explícitamente tras revisar las 21 categorías con su conteo |
| 2026-09-12 | `turno` de `HISTORICO ACCIDENTES`, 32 filas con `"-"` | Recodificado a `NA` dentro de `normalize_turno()` | Mismo criterio ya aplicado en `sexo`/`gravedad`: `"-"` es un marcador de "no reportado", no una categoría informativa | Equipo, confirmado explícitamente |
| 2026-09-12 | `area_responsabilidad`/`contrata` de `HISTORICO ACCIDENTES`, 8 celdas | Puestas en `NA` | Auditoría de PII: nombre completo de una persona (1 caso con RUC) filtrado por error hacia una columna que no es de identidad — ver sección "Auditoría de PII" | Equipo, a raíz de auditoría explícita solicitada |
| 2026-09-12 | `descripcion_accidente` (4 fuentes) y `descripcion_incidente`/`danos_reales_o_potenciales` (incidentes) | Redactadas con `clean.redact_pii_libre()` | Auditoría de PII encontró nombres de personas y un DNI explícito en hasta 40.6% de las filas de algún archivo — ver sección "Auditoría de PII" para el detalle y limitaciones de la heurística | Equipo, a raíz de auditoría explícita solicitada |
| 2026-09-12 | `edad_anios` (histórico, 4 filas), `tiempo_experiencia_meses` (2024, 2 filas), `dias_perdidos`/`dias_mas_ansi` (histórico, 4 filas) | Corregidas a `NA` en `src/ingest.py`, sin imputar reemplazo | Cada una viola una regla de negocio verificable (edad ≤0 imposible; experiencia en años > edad imposible; 6000 repetido en filas no relacionadas es un valor de sistema, no un dato real) — no se tocó ningún otro outlier IQR sin esa verificación | Equipo, criterio: solo corregir violaciones de regla de negocio confirmadas, no todo extremo estadístico |
| 2026-09-12 | Columnas con >80% de nulos en cualquiera de las 5 fuentes (`item`, `nro_rom`, `cargo_ansi`, `tipo_contacto`, `nota_midot`, `modalidad`, `horas_trabajadas_turno`, `es_verificado`, etc.) | Se quedan en `data/processed/` sin eliminar | En esta fase (EDA/limpieza, sin modelar) no se elimina ninguna columna del dataset — la decisión de qué X usar se toma en la fase de modelado, no antes. Se marcan como "no recomendadas como X por baja cobertura" en el diccionario, no se borran del CSV | Equipo, criterio: no restringir el dataset antes de que exista una necesidad de modelado concreta |
| 2026-09-12 | `lugar`, `fuente_peligro`, `puesto_trabajo` (histórico, 344-371 categorías) | Se difiere el agrupamiento — no se fuerza ninguna regla | A diferencia de `turno` (sinónimos obvios de un mismo número/franja), agrupar estas 3 columnas requiere criterio de dominio de SST/planta (qué lugares o peligros son "lo mismo") que no está disponible — inventarlo sería una decisión de negocio no verificable, mismo motivo por el que no se unificó turno numerado con franja horaria | Equipo, mismo criterio que la decisión de `turno` |

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

## Incidente de PII (2026-09-12)

### Qué se encontró

Una auditoría completa de las 5 fuentes procesadas encontró PII real sin
anonimizar en dos lugares que no eran columnas de identidad:

1. **`area_responsabilidad` y `contrata`** de `accidentes_historico_2012_2022.csv`:
   8 celdas con nombre completo de una persona (en un caso junto a su RUC),
   filtrado por error hacia una columna que no pasa por `anonymize_column()`.
2. **`descripcion_accidente`** (accidentes_2023/2024/historico/2025_2026) y
   **`descripcion_incidente`** (incidentes_2025_2026): texto libre con
   nombres de trabajadores, supervisores, choferes e incluso un DNI
   explícito, mencionados dentro de la narración del evento — hasta 40.6%
   de las filas en algún archivo.

Esta data ya estaba commiteada y pusheada a `develop` desde antes de esta
auditoría (fuentes agregadas en el PR #4), es decir, el incidente no fue
introducido por el trabajo de este hito — se descubrió al construir el EDA
dirigido (`02_eda_dirigido.ipynb`), al revisar el detalle de la columna
`area_responsabilidad` en una tabla de contingencia.

### Cómo se detectó

Barrido programático sobre las 5 fuentes procesadas, sin corregir nada hasta
confirmar el alcance completo:
1. Búsqueda de patrones de 8 dígitos (DNI) y 10-11 dígitos (RUC), literal y
   junto a las palabras "DNI"/"RUC", en todas las columnas de texto.
2. Revisión de las categorías de cada columna categórica (finitas, se pueden
   inspeccionar a mano) buscando valores con estructura de nombre propio.
3. Heurística de texto libre: secuencias de 2 a 4 palabras en Título-Caso en
   `descripcion_accidente`/`descripcion_incidente`/`danos_reales_o_potenciales`,
   con clasificación manual de cuáles son nombres reales vs. falsos positivos
   (lugares, clínicas, empresas).

### Cómo se remedió

- Las 8 celdas puntuales de `area_responsabilidad`/`contrata` se pusieron en
  `NA` en `src/ingest.py` (`_CELDAS_PII_HISTORICO`), mismo criterio que las
  celdas mal pegadas ya documentadas arriba.
- Se creó `clean.redact_pii_libre()`, aplicada a `descripcion_accidente` (en
  las 4 fuentes que la tienen) y a `descripcion_incidente` /
  `danos_reales_o_potenciales` (en incidentes): reemplaza DNI/RUC
  etiquetados por `[DNI]`/`[RUC]`, y secuencias de 2-4 palabras en
  Título-Caso por `[NOMBRE]`.

- Las 8 celdas puntuales de `area_responsabilidad`/`contrata` se pusieron en
  `NA` en `src/ingest.py` (`_CELDAS_PII_HISTORICO`), mismo criterio que las
  celdas mal pegadas ya documentadas arriba.
- Se creó `clean.redact_pii_libre()`, aplicada a `descripcion_accidente` (en
  las 4 fuentes que la tienen) y a `descripcion_incidente` /
  `danos_reales_o_potenciales` (en incidentes): reemplaza DNI/RUC
  etiquetados por `[DNI]`/`[RUC]`, y secuencias de 2-4 palabras en
  Título-Caso por `[NOMBRE]`.

**⚠️ Limitación explícita — es una heurística, no un NER validado:**

- Puede enmascarar nombres de lugar/clínica/empresa que también están en
  Título-Caso (falso positivo, ej. "Molino Santa Rosa" → `[NOMBRE]`). Se
  prioriza no dejar pasar un nombre de persona sobre preservar esos
  términos — el texto queda menos legible pero más seguro.
- Puede no detectar un nombre que no siga el patrón esperado: una sola
  palabra suelta después de un nombre de 4 palabras ya enmascarado (ej.
  "[NOMBRE] Jhon"), o nombres en minúscula.
- Verificado tras aplicarla: 0 coincidencias reales de nombre/DNI/RUC
  residuales en los 5 CSV (los únicos "positivos" del re-chequeo fueron 3
  falsos positivos benignos: ceros de un timestamp, un nombre de
  laboratorio, y un número de viaje interno — ninguno es PII).
- **Sigue pendiente una revisión humana** de una muestra antes de compartir
  estas columnas fuera del equipo (ej. en una presentación o un PDF
  exportado) — esta redacción automática reduce el riesgo, no lo elimina
  por completo.
