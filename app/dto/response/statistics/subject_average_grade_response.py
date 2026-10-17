from decimal import Decimal
from pydantic import BaseModel


class SubjectAverageGradeResponse(BaseModel):
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    average_grade: Decimal
    total_grades: int
