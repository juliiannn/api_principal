from datetime import date
from pydantic import BaseModel
from app.model import EnrollmentStatus


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    course_id: int
    course_name: str
    enrollment_date: date
    status: EnrollmentStatus
