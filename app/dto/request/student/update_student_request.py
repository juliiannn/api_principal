from pydantic import EmailStr, field_validator
from app.dto.camel_model import CamelModel
from app.dto.validators import validate_digits


class UpdateStudentRequest(CamelModel):
    guardian_name: str
    guardian_phone: str
    guardian_email: EmailStr

    @field_validator("guardian_phone")
    @classmethod
    def _gphone(cls, v): return validate_digits(v, "Guardian phone")
