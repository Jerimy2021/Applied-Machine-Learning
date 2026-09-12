"""
Esquema de columnas del proyecto.

Declara cada columna que existe en cada CSV de data/processed/: su tipo
esperado y a qué fuente(s) pertenece. Ver la descripción completa de cada
una en reports/diccionario_datos.md — este archivo es la versión "para
código" de esa documentación (ej. para validar un DataFrame antes de
usarlo).

- ESQUEMA_ACCIDENTES: accidentes_2023.csv / accidentes_2024.csv
- ESQUEMA_HISTORICO: accidentes_historico_2012_2022.csv
- ESQUEMA_TABLERO_ACCIDENTES: accidentes_2025_2026.csv
- ESQUEMA_INCIDENTES: incidentes_2025_2026.csv
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
    Columna("es_recategorizado", "boolean", ("2024",)),
    Columna("id_persona", "str", ("2023", "2024")),  # anonimizado, ver diccionario_datos.md
    Columna("fuente_archivo", "str", ("2023", "2024")),
)


def columnas_para(anio: str) -> list[str]:
    """Nombres de columna esperados para un año dado ('2023' o '2024')."""
    return [c.nombre for c in ESQUEMA_ACCIDENTES if anio in c.anios]


# ---------------------------------------------------------------------------
# Las 3 fuentes adicionales (ver src/ingest.py) tienen esquemas de columnas
# muy distintos entre sí y respecto a ESQUEMA_ACCIDENTES, por eso se declaran
# por separado en vez de forzarlos a la misma tupla. Ver el detalle de cada
# columna en reports/diccionario_datos.md.
# ---------------------------------------------------------------------------

ESQUEMA_HISTORICO: tuple[Columna, ...] = (
    Columna("nro_rom", "str", ("historico",)),
    Columna("programa", "category", ("historico",)),
    Columna("lugar", "category", ("historico",)),
    Columna("area_responsabilidad", "category", ("historico",)),
    Columna("id_persona", "str", ("historico",)),  # anonimizado
    Columna("edad_anios", "float64", ("historico",)),
    Columna("puesto_trabajo", "category", ("historico",)),
    Columna("sexo", "category", ("historico",)),
    Columna("turno", "category", ("historico",)),
    Columna("experiencia_puesto", "object", ("historico",)),
    Columna("fecha_evento", "datetime64[ns]", ("historico",)),
    Columna("gravedad", "category", ("historico",)),
    Columna("descripcion_accidente", "str", ("historico",)),
    Columna("parte_cuerpo_afectada", "category", ("historico",)),
    Columna("anio", "int64", ("historico",)),
    Columna("mes", "category", ("historico",)),
    Columna("dias_perdidos", "float64", ("historico",)),
    Columna("cargo_ansi", "category", ("historico",)),
    Columna("dias_mas_ansi", "float64", ("historico",)),
    Columna("fuente_peligro", "category", ("historico",)),
    Columna("actividad_realizada", "category", ("historico",)),
    Columna("tipo_contacto", "category", ("historico",)),  # 100% nulo, ver diccionario
    Columna("dano", "category", ("historico",)),
    Columna("contrata", "category", ("historico",)),
    Columna("nota_midot", "float64", ("historico",)),
    Columna("modalidad", "category", ("historico",)),
    Columna("fuente_archivo", "str", ("historico",)),
)

ESQUEMA_TABLERO_ACCIDENTES: tuple[Columna, ...] = (
    Columna("nro_rom", "str", ("2025_2026",)),
    Columna("sociedad", "category", ("2025_2026",)),
    Columna("vicepresidencia", "category", ("2025_2026",)),
    Columna("direccion", "category", ("2025_2026",)),
    Columna("categoria", "category", ("2025_2026",)),
    Columna("planta", "category", ("2025_2026",)),
    Columna("planta_sigma", "category", ("2025_2026",)),
    Columna("fecha_evento", "datetime64[ns]", ("2025_2026",)),
    Columna("hora", "object", ("2025_2026",)),
    Columna("turno", "category", ("2025_2026",)),
    Columna("dia_semana", "category", ("2025_2026",)),
    Columna("edad_anios", "float64", ("2025_2026",)),
    Columna("tiempo_empresa_meses", "float64", ("2025_2026",)),
    Columna("tiempo_empresa_anios", "float64", ("2025_2026",)),
    Columna("horas_trabajadas_turno", "float64", ("2025_2026",)),
    Columna("area", "category", ("2025_2026",)),
    Columna("empresa", "category", ("2025_2026",)),
    Columna("tipo_trabajador", "category", ("2025_2026",)),
    Columna("descripcion_accidente", "str", ("2025_2026",)),
    Columna("lesion", "category", ("2025_2026",)),
    Columna("dias_registrables", "int64", ("2025_2026",)),
    Columna("fuente_peligro", "category", ("2025_2026",)),
    Columna("causa_basica", "category", ("2025_2026",)),
    Columna("causa_principal", "category", ("2025_2026",)),
    Columna("causa_inmediata", "category", ("2025_2026",)),
    Columna("trimestre", "category", ("2025_2026",)),
    Columna("es_hard_stop", "boolean", ("2025_2026",)),
    Columna("id_persona", "str", ("2025_2026",)),  # anonimizado
    Columna("fuente_archivo", "str", ("2025_2026",)),
)

ESQUEMA_INCIDENTES: tuple[Columna, ...] = (
    Columna("planta", "category", ("2025_2026",)),
    Columna("fecha_evento", "datetime64[ns]", ("2025_2026",)),
    Columna("empresa", "category", ("2025_2026",)),
    Columna("tipo_evento", "category", ("2025_2026",)),
    Columna("descripcion_incidente", "str", ("2025_2026",)),
    Columna("danos_reales_o_potenciales", "str", ("2025_2026",)),
    Columna("fuente_peligro", "category", ("2025_2026",)),
    Columna("es_verificado", "boolean", ("2025_2026",)),
    Columna("fuente_archivo", "str", ("2025_2026",)),
)
