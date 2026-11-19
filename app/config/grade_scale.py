"""Escala de notas del colegio (SIEE, Decreto 1290 de 2009). Notas de 0 a 10.

Un solo lugar para la nota mínima aprobatoria: la usan las alertas por correo, los reportes Excel/PDF
y los niveles de desempeño. Se puede cambiar con la variable PASSING_GRADE del .env (por defecto 6.5).
"""
from app.config.settings import settings

PASSING_GRADE: float = settings.PASSING_GRADE   # menor a esto = desempeño Bajo (no aprueba)
HIGH_GRADE: float = 8.0                        # desde aquí, desempeño Alto
SUPERIOR_GRADE: float = 9.5                    # desde aquí, desempeño Superior


def is_failing(value: float) -> bool:
    return value is not None and float(value) < PASSING_GRADE


def level_of(avg: float) -> str:
    """Superior ≥ 9.5 · Alto ≥ 8.0 · Básico ≥ nota mínima · Bajo < nota mínima."""
    if avg >= SUPERIOR_GRADE:
        return "Superior"
    if avg >= HIGH_GRADE:
        return "Alto"
    return "Básico" if avg >= PASSING_GRADE else "Bajo"


def fmt(value: float) -> str:
    """6.5 → "6,5" (como se escribe en Colombia)."""
    return f"{value:.1f}".replace(".", ",")
