from app.dto.camel_model import CamelModel
from app.model import UserRole


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    must_change_password: bool
    role: UserRole
