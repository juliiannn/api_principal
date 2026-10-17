from datetime import time
from pydantic import BaseModel
from app.model import DayOfWeek


class CreateScheduleRequest(BaseModel):
    course_subject_id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
