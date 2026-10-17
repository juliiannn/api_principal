from datetime import time
from pydantic import BaseModel
from app.model import DayOfWeek


class ScheduleResponse(BaseModel):
    id: int
    course_subject_id: int
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    teacher_id: int
    teacher_name: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
