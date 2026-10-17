from datetime import date
from pydantic import BaseModel
from app.model import EducationLevel, CoordinationArea


class CoordinatorResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    employee_code: str
    area: CoordinationArea
    assignment_date: date
    education_level: EducationLevel
