from app.dto.camel_model import CamelModel


class CourseSubjectResponse(CamelModel):
    id: int
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    teacher_id: int
    teacher_name: str
    estado: bool
