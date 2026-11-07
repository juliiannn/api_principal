from app.dto.camel_model import CamelModel
from app.model import PermissionScope


class UpdateRoleModuleRequest(CamelModel):
    puede_ver: bool = False
    puede_crear: bool = False
    puede_editar: bool = False
    puede_eliminar: bool = False
    alcance: PermissionScope = PermissionScope.ALL
