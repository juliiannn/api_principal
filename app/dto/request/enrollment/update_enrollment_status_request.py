from pydantic import BaseModel
from app.model import EnrollmentStatus


class UpdateEnrollmentStatusRequest(BaseModel):
    status: EnrollmentStatus
