from typing import Optional
from app.dto.camel_model import CamelModel


class CreateCourseRequest(CamelModel):
    name: str
    grade: str
    classroom: str
    school_year: int
    director_teacher_id: Optional[int] = None
