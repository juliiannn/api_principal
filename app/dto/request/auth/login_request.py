from pydantic import EmailStr
from app.dto.camel_model import CamelModel


class LoginRequest(CamelModel):
    email: EmailStr
    password: str
