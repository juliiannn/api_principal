from typing import Optional
from pydantic import BaseModel


class CourseResponse(BaseModel):
    id: int
    name: str
    grade: str
    classroom: str
    school_year: int
    director_teacher_id: Optional[int]
    director_teacher_name: Optional[str]
    estado: bool
