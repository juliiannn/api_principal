from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.model import UserRole, DocumentType, Gender


class UserResponse(BaseModel):
    id: int
    document_type: DocumentType
    document: str
    email: str
    full_name: str
    phone: str
    birth_date: date
    gender: Gender
    address: str
    enabled: bool
    must_change_password: bool
    role: UserRole
    estado: bool = True
    creado: Optional[datetime] = None

    class Config:
        from_attributes = True
