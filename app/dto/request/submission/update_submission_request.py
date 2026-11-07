from pydantic import field_validator
from app.dto.camel_model import CamelModel


class UpdateSubmissionRequest(CamelModel):
    contenido: str

    @field_validator("contenido")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content must not be blank")
        return v
