from pydantic import BaseModel


class TransferEnrollmentRequest(BaseModel):
    student_id: int
    new_course_id: int
