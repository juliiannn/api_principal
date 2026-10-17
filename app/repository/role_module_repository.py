from typing import List, Optional

from app.model import Module, RoleModule
from app.repository.base_repository import BaseRepository


class RoleModuleRepository(BaseRepository):

    def find_active_by_id(self, rm_id: int) -> Optional[RoleModule]:
        return self.db.query(RoleModule).filter(RoleModule.id == rm_id, RoleModule.estado.is_(True)).first()

    def find_by_role_and_module(self, role_id: int, module_id: int) -> Optional[RoleModule]:
        return self.db.query(RoleModule).filter(
            RoleModule.role_id == role_id, RoleModule.module_id == module_id
        ).first()

    def find_all_active(self, role_id: Optional[int] = None) -> List[RoleModule]:
        q = self.db.query(RoleModule).filter(RoleModule.estado.is_(True))
        if role_id is not None:
            q = q.filter(RoleModule.role_id == role_id)
        return q.all()

    def find_permission(self, role_id: int, module_name: str) -> Optional[RoleModule]:
        """Permiso activo de un rol sobre un módulo (por nombre de módulo)."""
        return (
            self.db.query(RoleModule)
            .join(Module, RoleModule.module_id == Module.id)
            .filter(
                RoleModule.role_id == role_id,
                RoleModule.estado.is_(True),
                Module.nombre == module_name,
                Module.estado.is_(True),
            )
            .first()
        )

    def find_active_by_role(self, role_id: int) -> List[RoleModule]:
        """Todos los permisos activos del rol (para armar el menú del frontend)."""
        return (
            self.db.query(RoleModule)
            .join(Module, RoleModule.module_id == Module.id)
            .filter(
                RoleModule.role_id == role_id,
                RoleModule.estado.is_(True),
                Module.estado.is_(True),
            )
            .all()
        )
