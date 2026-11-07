from pydantic import ConfigDict
from app.dto.camel_model import CamelModel


class SubjectResponse(CamelModel):
    id: int
    name: str
    estado: bool

    model_config = ConfigDict(from_attributes=True)
