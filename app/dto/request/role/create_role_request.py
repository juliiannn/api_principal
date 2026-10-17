from typing import Optional
from pydantic import BaseModel


class CreateRoleRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
