# Proyecto: Análisis Predictivo de Accidentes SST

## Contexto
Curso de Machine Learning Aplicado — Ingeniería Industrial.
Equipo con background industrial, NO de software. El código debe ser legible
y comentado en español; los nombres de variables/funciones en inglés o snake_case.

## Estado actual
Fase 1: Ingesta, EDA y limpieza. NO se entrenan modelos todavía.

## Reglas duras
- `data/raw/` es SOLO LECTURA. Jamás modificar ni sobrescribir un archivo ahí.
- Ningún archivo de `data/` se commitea. Verificar `.gitignore` antes de `git add`.
- Nunca inventar el contenido de un archivo: leerlo primero y reportar lo que hay.
- Toda decisión de limpieza (imputación, eliminación, recodificación) se registra
  en `reports/diccionario_datos.md` con su justificación.
- Prohibido imputar silenciosamente. Si hay nulos, primero reportarlos y preguntar.
- La lógica reutilizable va en `src/`. Los notebooks solo importan y muestran.

## Estándar de columnas
- snake_case, sin tildes, sin ñ, sin espacios: `dias_perdidos`, `parte_cuerpo_afectada`
- Fechas: `datetime64`, columna `fecha_evento`
- Categóricas: `category`, valores normalizados en MAYÚSCULAS sin tildes
- Booleanas: prefijo `es_` o `tiene_`
- Toda columna del diccionario declarada en `src/schema.py`

## Confidencialidad
Data real de una empresa. Anonimizar nombres, DNI y legajos antes de cualquier
salida que se comparta. Usar hash o ID sintético.

## Git
Ramas: main (protegida) ← develop ← feature/*
Commits: Conventional Commits. No commitear directo a develop sin PR.
