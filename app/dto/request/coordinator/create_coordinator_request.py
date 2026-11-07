from datetime import date
from app.model import EducationLevel, CoordinationArea
from app.dto.request.person.base_person_request import BasePersonRequest


class CreateCoordinatorRequest(BasePersonRequest):
    employee_code: str
    area: CoordinationArea
    assignment_date: date
    education_level: EducationLevel
