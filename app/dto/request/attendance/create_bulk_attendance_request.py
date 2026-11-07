from datetime import date
from typing import List
from app.dto.camel_model import CamelModel
from app.dto.request.attendance.bulk_attendance_record import BulkAttendanceRecord


class CreateBulkAttendanceRequest(CamelModel):
    course_subject_id: int
    date: date
    records: List[BulkAttendanceRecord]
