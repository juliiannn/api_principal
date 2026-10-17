from datetime import date
from pydantic import BaseModel
from app.model import EducationLevel, ContractType


class UpdateTeacherRequest(BaseModel):
    employee_code: str
    hire_date: date
    profession: str
    specialty: str
    education_level: EducationLevel
    contract_type: ContractType
