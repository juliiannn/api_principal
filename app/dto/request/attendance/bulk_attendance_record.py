from app.dto.camel_model import CamelModel
from app.model import AttendanceStatus


class BulkAttendanceRecord(CamelModel):
    student_id: int
    status: AttendanceStatus
