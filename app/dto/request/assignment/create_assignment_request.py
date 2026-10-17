from datetime import date
from pydantic import BaseModel


class CreateAssignmentRequest(BaseModel):
    course_subject_id: int
    title: str
    description: str
    due_date: date
