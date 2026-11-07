from decimal import Decimal

from pydantic import field_validator
from app.dto.camel_model import CamelModel


class GradeSubmissionRequest(CamelModel):
    nota: Decimal
    retroalimentacion: str

    @field_validator("nota")
    @classmethod
    def _range(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.0") or v > Decimal("10.0"):
            raise ValueError("Grade must be between 0.0 and 10.0")
        return v

    @field_validator("retroalimentacion")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Feedback must not be blank")
        return v
