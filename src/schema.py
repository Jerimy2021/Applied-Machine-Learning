"""
Esquema de columnas del proyecto.

Declara cada columna que existe en data/processed/accidentes_2023.csv y
data/processed/accidentes_2024.csv: su tipo esperado y a qué año(s)
pertenece. Ver la descripción completa de cada una en
reports/diccionario_datos.md — este archivo es la versión "para código"
de esa documentación (ej. para validar un DataFrame antes de usarlo).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Columna:
    nombre: str
    dtype: str  # tal como pandas lo reporta: float64, category, datetime64[ns], str, bool
    anios: tuple[str, ...]  # ("2023", "2024") o solo uno de los dos


ESQUEMA_ACCIDENTES: tuple[Columna, ...] = (
    Columna("item", "float64", ("2023", "2024")),
    Columna("nro_rom", "str", ("2023", "2024")),
    Columna("pais", "category", ("2023", "2024")),
    Columna("sociedad", "category", ("2023", "2024")),
    Columna("predio", "category", ("2023", "2024")),
    Columna("planta", "category", ("2023", "2024")),
    Columna("planta_sigma", "category", ("2024",)),
    Columna("direccion", "category", ("2023", "2024")),
    Columna("area", "category", ("2023", "2024")),
    Columna("tipo_accidente", "category", ("2024",)),
    Columna("tipo_accidente_2", "category", ("2024",)),
    Columna("tipo_accidente_3", "category", ("2024",)),
    Columna("fecha_evento", "datetime64[ns]", ("2023", "2024")),
    Columna("semana", "float64", ("2023", "2024")),
    Columna("dia", "float64", ("2023", "2024")),
    Columna("mes", "float64", ("2023", "2024")),
    Columna("anio", "float64", ("2023", "2024")),
    Columna("hora", "object", ("2023", "2024")),
    Columna("turno", "category", ("2023", "2024")),
    Columna("tipo_trabajador", "category", ("2023", "2024")),
    Columna("empresa", "category", ("2023", "2024")),
    Columna("sexo", "category", ("2023", "2024")),
    Columna("edad_anios", "float64", ("2023", "2024")),
    Columna("puesto_trabajo", "category", ("2023", "2024")),
    Columna("fecha_ingreso_labores", "datetime64[ns]", ("2023", "2024")),
    Columna("descripcion_accidente", "str", ("2023", "2024")),
    Columna("tipo_contacto", "category", ("2023", "2024")),
    Columna("parte_cuerpo_afectada", "category", ("2023", "2024")),
    Columna("parte_cuerpo_afectada_2", "category", ("2023", "2024")),
    Columna("actividad_realizada", "category", ("2023", "2024")),
    Columna("proceso", "category", ("2023",)),
    Columna("diagnostico_medico", "category", ("2023", "2024")),
    Columna("lesion", "category", ("2023", "2024")),
    Columna("dias_dm", "float64", ("2023", "2024")),
    Columna("cargo_ansi", "category", ("2023", "2024")),
    Columna("dias_dm_total_indicador", "float64", ("2023", "2024")),
    Columna("situacion_actual", "category", ("2023", "2024")),
    Columna("tiempo_experiencia_meses", "float64", ("2023", "2024")),
    Columna("puesto", "category", ("2023",)),
    Columna("antiguedad", "category", ("2023", "2024")),
    Columna("fuente_peligro", "category", ("2023", "2024")),
    Columna("tipo_contrato", "category", ("2023", "2024")),
    Columna("poblacion", "float64", ("2024",)),
    Columna("es_considerado", "boolean", ("2024",)),
    Columna("es_recategorizado", "bool", ("2024",)),
    Columna("id_persona", "str", ("2023", "2024")),  # anonimizado, ver diccionario_datos.md
    Columna("fuente_archivo", "str", ("2023", "2024")),
)


def columnas_para(anio: str) -> list[str]:
    """Nombres de columna esperados para un año dado ('2023' o '2024')."""
    return [c.nombre for c in ESQUEMA_ACCIDENTES if anio in c.anios]
