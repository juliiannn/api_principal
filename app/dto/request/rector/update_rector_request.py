from datetime import date
from app.dto.camel_model import CamelModel
from app.model import EducationLevel


class UpdateRectorRequest(CamelModel):
    employee_code: str
    appointment_date: date
    administrative_period: str
    education_level: EducationLevel
