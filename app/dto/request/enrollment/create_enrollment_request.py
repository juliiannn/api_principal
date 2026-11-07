from app.dto.camel_model import CamelModel


class CreateEnrollmentRequest(CamelModel):
    student_id: int
    course_id: int
