from app.dto.camel_model import CamelModel


class CreateCourseSubjectRequest(CamelModel):
    course_id: int
    subject_id: int
    teacher_id: int
