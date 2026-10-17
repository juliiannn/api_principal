from datetime import date
from pydantic import BaseModel, EmailStr
from app.model import DocumentType, Gender


class UpdateUserRequest(BaseModel):
    document_type: DocumentType
    document: str
    email: EmailStr
    full_name: str
    phone: str
    birth_date: date
    gender: Gender
    address: str
