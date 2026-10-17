from pydantic import BaseModel


class CreateCourseSubjectRequest(BaseModel):
    course_id: int
    subject_id: int
    teacher_id: int
