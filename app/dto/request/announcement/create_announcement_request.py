from pydantic import field_validator
from app.dto.camel_model import CamelModel


class CreateAnnouncementRequest(CamelModel):
    titulo: str
    contenido: str

    @field_validator("titulo", "contenido")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be blank")
        return v
