from datetime import date
from pydantic import EmailStr
from app.dto.camel_model import CamelModel
from app.model import DocumentType, Gender


class UpdateUserRequest(CamelModel):
    document_type: DocumentType
    document: str
    email: EmailStr
    full_name: str
    phone: str
    birth_date: date
    gender: Gender
    address: str
