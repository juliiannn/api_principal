from pydantic import BaseModel


class CourseSubjectResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    teacher_id: int
    teacher_name: str
    estado: bool
