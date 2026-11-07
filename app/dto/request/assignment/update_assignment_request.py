from datetime import date

from app.dto.camel_model import CamelModel


class UpdateAssignmentRequest(CamelModel):
    title: str
    description: str
    due_date: date
