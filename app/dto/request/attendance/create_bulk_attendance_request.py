from datetime import date
from typing import List
from pydantic import BaseModel
from app.dto.request.attendance.bulk_attendance_record import BulkAttendanceRecord


class CreateBulkAttendanceRequest(BaseModel):
    course_subject_id: int
    date: date
    records: List[BulkAttendanceRecord]
