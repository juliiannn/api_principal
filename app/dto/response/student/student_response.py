from datetime import datetime
from typing import Optional
from app.model import DocumentType, Gender
from datetime import date
from app.dto.camel_model import CamelModel


class StudentResponse(CamelModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    document_type: Optional[DocumentType] = None
    gender: Optional[Gender] = None
    address: Optional[str] = None
    estado: bool = True
    creado: Optional[datetime] = None
    actualizado: Optional[datetime] = None
    guardian_name: str
    guardian_phone: str
    guardian_email: str
