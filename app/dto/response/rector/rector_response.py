from datetime import date
from pydantic import BaseModel
from app.model import EducationLevel


class RectorResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    employee_code: str
    appointment_date: date
    administrative_period: str
    education_level: EducationLevel
