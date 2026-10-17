from datetime import date
from pydantic import BaseModel, EmailStr, field_validator
from app.model import DocumentType, Gender
from app.dto.validators import validate_digits, validate_document_format, validate_past_date


class BasePersonRequest(BaseModel):
    document_type: DocumentType
    document: str
    email: EmailStr
    full_name: str
    phone: str
    birth_date: date
    gender: Gender
    address: str

    @field_validator("document")
    @classmethod
    def _doc(cls, v): return validate_document_format(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v): return validate_digits(v, "Phone")

    @field_validator("birth_date")
    @classmethod
    def _birth(cls, v): return validate_past_date(v)
