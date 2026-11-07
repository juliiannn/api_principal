from datetime import date
from app.model import EducationLevel, ContractType
from app.dto.request.person.base_person_request import BasePersonRequest


class CreateTeacherRequest(BasePersonRequest):
    employee_code: str
    hire_date: date
    profession: str
    specialty: str
    education_level: EducationLevel
    contract_type: ContractType
