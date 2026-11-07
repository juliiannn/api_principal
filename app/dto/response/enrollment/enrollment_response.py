from datetime import date
from app.dto.camel_model import CamelModel
from app.model import EnrollmentStatus


class EnrollmentResponse(CamelModel):
    id: int
    student_id: int
    student_name: str
    course_id: int
    course_name: str
    enrollment_date: date
    status: EnrollmentStatus
