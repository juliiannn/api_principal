from datetime import date
from app.dto.camel_model import CamelModel
from app.model import AttendanceStatus


class AttendanceResponse(CamelModel):
    id: int
    student_id: int
    student_name: str
    course_subject_id: int
    subject_name: str
    course_name: str
    date: date
    status: AttendanceStatus
