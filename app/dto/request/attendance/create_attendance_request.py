from datetime import date
from app.dto.camel_model import CamelModel
from app.model import AttendanceStatus


class CreateAttendanceRequest(CamelModel):
    student_id: int
    course_subject_id: int
    date: date
    status: AttendanceStatus
