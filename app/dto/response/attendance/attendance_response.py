from datetime import date
from pydantic import BaseModel
from app.model import AttendanceStatus


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    course_subject_id: int
    subject_name: str
    course_name: str
    date: date
    status: AttendanceStatus
