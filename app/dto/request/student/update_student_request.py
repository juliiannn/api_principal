from pydantic import BaseModel, EmailStr, field_validator
from app.dto.validators import validate_digits


class UpdateStudentRequest(BaseModel):
    guardian_name: str
    guardian_phone: str
    guardian_email: EmailStr

    @field_validator("guardian_phone")
    @classmethod
    def _gphone(cls, v): return validate_digits(v, "Guardian phone")
