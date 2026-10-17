from pydantic import BaseModel
from app.model import UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    must_change_password: bool
    role: UserRole
