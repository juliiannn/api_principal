from app.dto.camel_model import CamelModel


class TransferEnrollmentRequest(CamelModel):
    student_id: int
    new_course_id: int
