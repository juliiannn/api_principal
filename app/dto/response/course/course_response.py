from typing import Optional
from app.dto.camel_model import CamelModel


class CourseResponse(CamelModel):
    id: int
    name: str
    grade: str
    classroom: str
    school_year: int
    director_teacher_id: Optional[int]
    director_teacher_name: Optional[str]
    estado: bool
