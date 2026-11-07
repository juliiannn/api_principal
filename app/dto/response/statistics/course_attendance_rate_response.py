from decimal import Decimal
from app.dto.camel_model import CamelModel


class CourseAttendanceRateResponse(CamelModel):
    course_id: int
    course_name: str
    attendance_rate: Decimal
    total_records: int
