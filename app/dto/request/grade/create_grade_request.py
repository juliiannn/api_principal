from decimal import Decimal
from pydantic import BaseModel, field_validator
from app.model import Period


class CreateGradeRequest(BaseModel):
    student_id: int
    course_subject_id: int
    period: Period
    value: Decimal

    @field_validator("value")
    @classmethod
    def _range(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.0") or v > Decimal("10.0"):
            raise ValueError("Grade must be between 0.0 and 10.0")
        return v
