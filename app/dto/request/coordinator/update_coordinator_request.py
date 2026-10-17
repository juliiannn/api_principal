from datetime import date
from pydantic import BaseModel
from app.model import EducationLevel, CoordinationArea


class UpdateCoordinatorRequest(BaseModel):
    employee_code: str
    area: CoordinationArea
    assignment_date: date
    education_level: EducationLevel
