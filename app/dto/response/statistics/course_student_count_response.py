from app.dto.camel_model import CamelModel


class CourseStudentCountResponse(CamelModel):
    course_id: int
    course_name: str
    student_count: int
