# Estrategia de Data Preparation

**Estado:** estrategia definida el 2026-09-20; **aún no aplicada** en código ni en
los datos. Fuente: `data/processed/accidentes_historico_2012_2022.csv`. Cada
decisión se registra en la bitácora de `reports/diccionario_datos.md` al
implementarse.

## 0. Decisiones de partida (aprobadas por el equipo)

### A. Población de entrenamiento: histórico 2019-2022

El registro de accidentes no incapacitantes empieza en 2019: entre 2012 y 2018
**las 452 filas con etiqueta son 100% incapacitantes**. Entrenar con toda la
serie haría que el modelo aprenda que antes de 2019 todo es incapacitante.

| Año | Filas con etiqueta | % incapacitante | No incapacitantes |
|---|---|---|---|
| 2012-2018 | 452 | 100% | 0 |
| 2019 | 222 | 49.1% | 113 |
| 2020 | 111 | 75.7% | 27 |
| 2021 | 118 | 92.4% | 9 |
| 2022 | 113 | 94.7% | 6 |

- **Se usan 564 filas** de 2019-2022: 409 incapacitantes / 155 no incapacitantes
  (72.5% / 27.5%). Quedan fuera las 452 filas de 2012-2018 y las 12 con
  `es_incapacitante = NA` (todas de 2019 en adelante).
- 73% de los no incapacitantes (113 de 155) son de 2019, y en 2022 hay solo 6.
  Por eso `anio` no es X y una partición temporal no es confiable.
- **Sumar 2024 queda como extensión posterior:** trae 182 filas con 0 días de
  descanso y 82 con más de 0. En 2019-2022, `es_incapacitante` coincide con
  `dias_perdidos > 0` en 458 de 459 filas. 2023 y 2025-2026 no aportan
  negativos (`dias_dm` nunca es 0 en 2023 y `dias_registrables` es al menos 1 en
  2025-2026).

### B. Variables predictoras (X)

En 2019-2022 la disponibilidad de algunas variables depende de la clase: si se
imputan o se marcan como nulo, el modelo aprende cómo se registró el dato y no
el riesgo.

| Variable | % con dato: incapacitantes / no incapacitantes | Decisión |
|---|---|---|
| `experiencia_puesto_meses` | 82 / 6.5 | **Se excluye** (solo 10 de 155 no incapacitantes tienen valor) |
| `sexo` | 33 / 91 | **Se excluye** |
| `area_responsabilidad` | 10 / 19 (87% nulo) | **Se excluye** |
| `edad_anios` | 45 / 83 | Se mantiene, con la salvaguarda de la sección 3.1 |
| `turno`, `programa`, `lugar`, `puesto_trabajo`, `fuente_peligro`, `actividad_realizada`, `mes` | 88-100 en ambas clases | Se mantienen |

**X final:** 1 numérica (`edad_anios`) y 7 categóricas. `anio` queda fuera.

## 3.1 Estrategia de limpieza de datos

### Valores nulos

**No se eliminan filas por nulos.** Conservar solo las filas completas (7 categóricas
+ `edad_anios`) deja 272 de 564 (48%) y 122 de los 155 no incapacitantes.

| Variable | % nulo (2019-2022) | Tratamiento |
|---|---|---|
| `edad_anios` | 44.7 | Imputación con la **mediana calculada en train**, **sin indicador de nulo** |
| `turno`, `programa`, `lugar`, `puesto_trabajo`, `fuente_peligro`, `actividad_realizada` | 5.1 / 0.5 / 10.8 / 6.4 / 8.2 / 3.0 | El nulo pasa a la categoría explícita `SIN_DATO`; no se inventa un valor |
| `mes` | 0 | Sin nulos |
| Filas con `es_incapacitante = NA` | 12 | Se excluyen de entrenamiento y evaluación; no se imputan |

**Salvaguarda de `edad_anios`:** 55% de los incapacitantes tienen la edad
imputada. Se comparará el modelo con y sin `edad_anios`; si el rendimiento
depende de la edad imputada, se descarta.

### Duplicados

- **Filas idénticas: 0.** Tampoco hay `nro_rom` repetido. No hay nada que eliminar.
- **Casi duplicados:** 3 eventos con varias filas (8 filas) tienen igual fecha y
  descripción, pero distinto `id_persona`: un mismo evento con varios trabajadores
  afectados. **No se eliminan**; se mantienen juntos en la partición (sección 3.6).
- **Para revisión de SST (no se eliminan):** 2 casos de una misma persona el mismo
  día con dos registros de distinta gravedad (2019-11-20 y 2019-12-09), posible
  doble registro con etiquetas inconsistentes.
- `id_persona` no es un identificador confiable: 32 filas comparten el hash de
  `"-"` y otras 11 otro marcador sin persona. No es X.

### Aumento de datos

**No se generará un dataset simulado (mock).** Las razones:
1. Un accidente inventado no es evidencia de SST, y el conjunto de prueba
   debe ser real.
2. Los datos actuales alcanzan para un primer modelo: 564 filas, con 124 no
   incapacitantes en train y 31 en test. Con 31 casos, el recall de esa clase
   tiene un intervalo de confianza amplio: se reportará con validación cruzada
   repetida en train y no solo con el test.
3. Si se necesitan más datos, la vía es **real**: sumar 2024 (182 no
   incapacitantes más), tras alinear esquemas y validar con SST que
   `días de descanso > 0` equivale a incapacitante.
4. Para el desbalance: `class_weight='balanced'` (no agrega filas). El
   sobremuestreo (SMOTE), si se probara, se aplica solo dentro de train.

## 3.2 Tratamiento de outliers

Se distinguen dos tipos, como en un valor fuera de rango fisiológico frente a un
extremo verdadero:

| Tipo | Ejemplo aquí | Tratamiento |
|---|---|---|
| **Error de digitación** (imposible por regla de negocio) | `edad_anios <= 0` | Se pasa a `NA` (no se elimina la fila) y se imputa como cualquier nulo. Ya aplicado en 4 filas |
| **Extremo válido** | Experiencia o días de descanso muy altos | Se conserva |

- **Técnica de detección: IQR (1.5 × IQR).** No supone normalidad ni se distorsiona
  con la asimetría, a diferencia del Z-score.
- **No se eliminan filas por ser extremas:** son accidentes reales y hay pocos datos.
- **`edad_anios`** (única X numérica): rango 18-63, asimetría 0.36, **0 valores fuera
  del IQR**. Todo cae en el rango laboral legal, sin errores pendientes.
- **`experiencia_puesto_meses`** está excluida de X. Si se reincorporara: 26 valores
  fuera del IQR (4%), ninguno con |z| > 3 tras `log1p` (extremos válidos), y una
  fila imposible (edad 25 con 300 meses de experiencia, o sea desde los 0 años) que
  pasaría a `NA`.
- **`dias_perdidos` / `dias_mas_ansi`** no son X (*data leakage*). Ver hallazgo 1.

## 3.3 Transformación de variables numéricas

**StandardScaler** (media 0, desviación 1) sobre `edad_anios`, ajustado solo con train.

- Min-Max no aporta ventaja aquí y es sensible a extremos: un valor atípico
  comprimiría al resto y los datos de test fuera del rango de train saldrían de [0, 1].
- `edad_anios` es casi simétrica (asimetría 0.36), no requiere transformación
  logarítmica.
- El modelo aún no está elegido: el escalado va dentro del pipeline y solo lo usan
  los modelos sensibles a la escala (regresión logística, SVM, KNN); los árboles
  no lo necesitan.
- Orden: imputar (mediana) y luego escalar.

## 3.4 Tratamiento de variables categóricas

**One-Hot Encoding** para las 7 variables, agrupando las categorías poco frecuentes
en `OTROS`. **No se usa Label Encoding**: impondría un orden artificial a
categorías nominales. Tampoco *target encoding*: con 564 filas sobreajusta y
arriesga fuga de información.

| Variable | Categorías (2019-2022) | Con 10 filas o más | Filas que caen en `OTROS` |
|---|---|---|---|
| `turno` | 3 (`DIA`, `TARDE`, `NOCHE`) | 3 | 0% |
| `mes` | 12 | 12 | 0% |
| `actividad_realizada` | 29 | 7 | 8% |
| `programa` | 65 | 18 | 20% |
| `puesto_trabajo` | 257 | 5 | 70% |
| `fuente_peligro` | 271 | 6 | 68% |
| `lugar` | 326 | 4 | 86% |

- **Regla:** `OneHotEncoder(min_frequency=10, handle_unknown='infrequent_if_exist')`,
  con las categorías aprendidas en train. Resultan unas 65 columnas.
- **`puesto_trabajo`, `fuente_peligro` y `lugar`** quedan con 68-86% de las filas
  en `OTROS`: aportan poca información. La selección de variables (solo con train)
  evaluará si se descartan.
- **Unificación de grafías previa** (recodificación a registrar en el diccionario):
  - `SETIEMBRE` → `SEPTIEMBRE` (mismo mes; deja `mes` en 12 categorías).
  - `DURANTE RUTINA DE TRABAJO` → `DURANTE SU RUTINA DE TRABAJO` (variante de
    redacción).
  - `TRASLADANDOSE` y `TRASLADANDOSE A PIE` **no** se unifican: sin criterio
    verificable de dominio, igual que el turno numerado y el de franja horaria.
- `turno` en 2019-2022 solo tiene franja horaria (`DIA`/`TARDE`/`NOCHE`): el turno
  numerado (`TURNO_1/2/3`) existe solo antes de 2019.

## 3.6 Separación de datos (Train / Test)

- **80% train / 20% test:** 451 y 113 filas (327/82 incapacitantes y 124/31 no
  incapacitantes).
- **Estratificada por `es_incapacitante`**, para conservar el 72.5% / 27.5% en ambos.
- **Reproducible:** `random_state=42`.
- **Eventos completos:** las filas del mismo evento (fecha y descripción iguales)
  van juntas a train o a test. Se usa `StratifiedGroupKFold(n_splits=5, shuffle=True,
  random_state=42)` y su primer pliegue como test.
- El test se usa **una sola vez**, al final. Los hiperparámetros se ajustan con
  validación cruzada estratificada solo en train.

**Prevención de *data leakage*.** Todo lo que aprende de los datos va dentro de un
`Pipeline` y se ajusta solo con train:

| Paso | Aprende de los datos | Ajuste |
|---|---|---|
| Recodificar nulos a `SIN_DATO` y unificar grafías | No (regla fija) | Antes de la partición |
| Imputación de `edad_anios` (mediana) | Sí | Solo train |
| `StandardScaler` | Sí | Solo train |
| `OneHotEncoder` y umbral de categorías raras | Sí | Solo train |
| Selección de variables | Sí | Dentro de la validación cruzada, solo train |
| `class_weight` y, si se probara, SMOTE | Sí | Solo train |

## Hallazgos que requieren decisión del equipo

1. **Los valores `6000` de `dias_perdidos`/`dias_mas_ansi` quizá no son
   placeholders.** La columna `cargo_ansi` toma valores estándar (60, 75, 100, 135,
   175, 200, 300, 400, 3000, 4500, 6000). El `4500` de 2020 es una amputación de
   brazo con `cargo_ansi = 4500`: es un dato real. De los cuatro `6000` que se
   pasaron a `NA`, el de 2021 es un accidente `MORTAL` con `cargo_ansi = 6000`
   (dato real); los otros tres (atropello 2018, golpe 2019, fractura de pierna 2022)
   no tienen `cargo_ansi` y parecen un código mal digitado. **No afecta al modelo**
   (no son X; el target sale de `gravedad`), pero contradice la justificación del
   diccionario. **Propuesta:** restaurar `dias_mas_ansi = 6000` en el caso `MORTAL`
   y confirmar los demás con SST.
2. **Posible doble registro** de una misma persona el mismo día con gravedad
   distinta (2 casos). Requiere confirmación de SST.
3. **Sumar 2024 al entrenamiento:** ya probado como experimento en
   `notebooks/04_modelado.ipynb` (población combinada de 828 filas, recall
   0.868 en test frente a 0.806 con 2019-2022 solo). El resultado es
   mejor, pero sigue dependiendo de que SST confirme la equivalencia
   `días de descanso > 0` = incapacitante para esta fuente; mientras tanto
   el modelo oficial del Hito 2 sigue siendo el de 2019-2022.
