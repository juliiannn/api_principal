from decimal import Decimal
from pydantic import BaseModel


class CourseAttendanceRateResponse(BaseModel):
    course_id: int
    course_name: str
    attendance_rate: Decimal
    total_records: int
