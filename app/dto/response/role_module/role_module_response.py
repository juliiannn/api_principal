from pydantic import BaseModel
from app.model import PermissionScope


class RoleModuleResponse(BaseModel):
    id: int
    role_id: int
    role_name: str
    module_id: int
    module_name: str
    puede_ver: bool
    puede_crear: bool
    puede_editar: bool
    puede_eliminar: bool
    alcance: PermissionScope
    estado: bool
