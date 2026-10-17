from pydantic import BaseModel
from app.model import PermissionScope


class MyPermissionResponse(BaseModel):
    """Módulos y permisos del usuario autenticado (para armar el menú del frontend)."""
    modulo: str
    ruta: str
    puede_ver: bool
    puede_crear: bool
    puede_editar: bool
    puede_eliminar: bool
    alcance: PermissionScope
