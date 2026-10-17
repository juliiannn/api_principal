from pydantic import BaseModel


class CourseStudentCountResponse(BaseModel):
    course_id: int
    course_name: str
    student_count: int
