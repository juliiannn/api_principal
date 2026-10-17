from datetime import date
from pydantic import BaseModel


class StudentResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    guardian_name: str
    guardian_phone: str
    guardian_email: str
