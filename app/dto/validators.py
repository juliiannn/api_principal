from datetime import date


def validate_digits(v: str, field_name: str = "Field") -> str:
    if not v.isdigit():
        raise ValueError(f"{field_name} must contain only numbers")
    return v


def validate_document_format(v: str) -> str:
    if not v.isdigit() or not (6 <= len(v) <= 15):
        raise ValueError("El documento debe tener entre 6 y 15 dígitos numéricos")
    return v


def validate_past_date(v: date) -> date:
    if v >= date.today():
        raise ValueError("La fecha debe ser en el pasado")
    return v
