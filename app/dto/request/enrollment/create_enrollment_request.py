from pydantic import BaseModel


class CreateEnrollmentRequest(BaseModel):
    student_id: int
    course_id: int
