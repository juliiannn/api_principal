from app.dto.camel_model import CamelModel


class CreateSubjectRequest(CamelModel):
    name: str
