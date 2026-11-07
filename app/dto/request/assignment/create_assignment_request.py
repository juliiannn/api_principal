from datetime import date
from app.dto.camel_model import CamelModel


class CreateAssignmentRequest(CamelModel):
    course_subject_id: int
    title: str
    description: str
    due_date: date
