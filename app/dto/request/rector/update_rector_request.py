from datetime import date
from pydantic import BaseModel
from app.model import EducationLevel


class UpdateRectorRequest(BaseModel):
    employee_code: str
    appointment_date: date
    administrative_period: str
    education_level: EducationLevel
