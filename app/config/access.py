from dataclasses import dataclass

from app.model import PermissionScope, User


@dataclass
class Access:
    """Resultado de una verificación de permiso: el usuario y el alcance con el que puede actuar."""
    user: User
    scope: PermissionScope
