from app.dto.camel_model import CamelModel
from app.model import PermissionScope


class RoleModuleRequest(CamelModel):
    role_id: int
    module_id: int
    puede_ver: bool = False
    puede_crear: bool = False
    puede_editar: bool = False
    puede_eliminar: bool = False
    alcance: PermissionScope = PermissionScope.ALL
