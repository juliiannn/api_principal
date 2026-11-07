from decimal import Decimal
from app.dto.camel_model import CamelModel
from app.model import Period


class GradeResponse(CamelModel):
    id: int
    student_id: int
    student_name: str
    course_subject_id: int
    subject_name: str
    course_name: str
    teacher_name: str
    period: Period
    value: Decimal
