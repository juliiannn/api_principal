from datetime import time
from app.dto.camel_model import CamelModel
from app.model import DayOfWeek


class CreateScheduleRequest(CamelModel):
    course_subject_id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
