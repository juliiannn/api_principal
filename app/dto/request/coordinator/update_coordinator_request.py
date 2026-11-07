from datetime import date
from app.dto.camel_model import CamelModel
from app.model import EducationLevel, CoordinationArea


class UpdateCoordinatorRequest(CamelModel):
    employee_code: str
    area: CoordinationArea
    assignment_date: date
    education_level: EducationLevel
