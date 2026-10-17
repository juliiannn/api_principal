from datetime import date
from app.model import EducationLevel
from app.dto.request.person.base_person_request import BasePersonRequest


class CreateRectorRequest(BasePersonRequest):
    employee_code: str
    appointment_date: date
    administrative_period: str
    education_level: EducationLevel
