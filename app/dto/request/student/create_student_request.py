from pydantic import EmailStr, field_validator
from app.dto.validators import validate_digits
from app.dto.request.person.base_person_request import BasePersonRequest


class CreateStudentRequest(BasePersonRequest):
    guardian_name: str
    guardian_phone: str
    guardian_email: EmailStr

    @field_validator("guardian_phone")
    @classmethod
    def _gphone(cls, v): return validate_digits(v, "Guardian phone")
