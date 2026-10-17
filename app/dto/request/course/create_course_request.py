from typing import Optional
from pydantic import BaseModel


class CreateCourseRequest(BaseModel):
    name: str
    grade: str
    classroom: str
    school_year: int
    director_teacher_id: Optional[int] = None
