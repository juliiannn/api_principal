from pydantic import BaseModel, field_validator


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_length(cls, v: str) -> str:
        if not (8 <= len(v) <= 72):
            raise ValueError("La contraseña debe tener entre 8 y 72 caracteres")
        return v
