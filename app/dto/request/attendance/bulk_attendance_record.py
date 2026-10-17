from pydantic import BaseModel
from app.model import AttendanceStatus


class BulkAttendanceRecord(BaseModel):
    student_id: int
    status: AttendanceStatus
