from datetime import date
from app.dto.camel_model import CamelModel
from app.model import EducationLevel, ContractType


class UpdateTeacherRequest(CamelModel):
    employee_code: str
    hire_date: date
    profession: str
    specialty: str
    education_level: EducationLevel
    contract_type: ContractType
