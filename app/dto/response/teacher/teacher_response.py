from datetime import date
from pydantic import BaseModel
from app.model import EducationLevel, ContractType


class TeacherResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    employee_code: str
    hire_date: date
    profession: str
    specialty: str
    education_level: EducationLevel
    contract_type: ContractType
