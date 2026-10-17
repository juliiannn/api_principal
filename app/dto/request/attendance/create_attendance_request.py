from datetime import date
from pydantic import BaseModel
from app.model import AttendanceStatus


class CreateAttendanceRequest(BaseModel):
    student_id: int
    course_subject_id: int
    date: date
    status: AttendanceStatus
