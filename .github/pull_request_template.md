## Descripción

<!-- ¿Qué cambia este PR y por qué? -->

## Tipo de cambio

- [ ] `feat` — nueva funcionalidad
- [ ] `fix` — corrección de bug
- [ ] `chore` — mantenimiento (config, dependencias, estructura)
- [ ] `docs` — documentación
- [ ] `refactor` — cambio de código sin alterar comportamiento

## Checklist

- [ ] El título del PR sigue Conventional Commits (`feat: ...`, `fix: ...`, etc.)
- [ ] `git ls-files data/` solo muestra `.csv` de `data/processed/` (nunca `data/raw/`, `data/interim/`, ni `.xlsx`/`.xls`) — ver [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] No se modificó ni sobrescribió ningún archivo de `data/raw/`
- [ ] Si hubo limpieza/imputación/recodificación, quedó documentada en `reports/diccionario_datos.md` con su justificación
- [ ] Si se agrega/modifica un `.csv` en `data/processed/`, pasó por `clean.anonymize_column()` en toda columna con datos personales
- [ ] Nombres de columnas nuevos siguen el estándar (snake_case, sin tildes/ñ) y están declarados en `src/schema.py`
- [ ] Cualquier salida compartible (notebook, figura, reporte) tiene los datos personales anonimizados
- [ ] La lógica reutilizable está en `src/`, los notebooks solo importan y muestran
- [ ] `uv run ruff check .` pasa sin errores

## Notas para el revisor

<!-- Contexto adicional, capturas, dudas puntuales, etc. -->
