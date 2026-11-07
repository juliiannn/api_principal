from decimal import Decimal
from app.dto.camel_model import CamelModel


class SubjectAverageGradeResponse(CamelModel):
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    average_grade: Decimal
    total_grades: int
