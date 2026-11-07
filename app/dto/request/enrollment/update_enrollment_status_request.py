from app.dto.camel_model import CamelModel
from app.model import EnrollmentStatus


class UpdateEnrollmentStatusRequest(CamelModel):
    status: EnrollmentStatus
