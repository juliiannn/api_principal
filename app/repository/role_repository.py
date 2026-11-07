from typing import List, Optional

from app.model import Role
from app.repository.base_repository import BaseRepository


class RoleRepository(BaseRepository):

    def find_by_id(self, role_id: int, include_inactive: bool = False) -> Optional[Role]:
        q = self.db.query(Role).filter(Role.id == role_id)
        if not include_inactive:
            q = q.filter(Role.estado.is_(True))
        return q.first()

    def find_all(self, include_inactive: bool = False) -> List[Role]:
        q = self.db.query(Role)
        if not include_inactive:
            q = q.filter(Role.estado.is_(True))
        return q.all()

    def find_active_by_name(self, nombre: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nombre == nombre, Role.estado.is_(True)).first()

    def find_by_name(self, nombre: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nombre == nombre).first()

    def exists_by_name(self, nombre: str) -> bool:
        return self.db.query(Role).filter(Role.nombre == nombre).first() is not None

    def exists_by_name_and_id_not(self, nombre: str, role_id: int) -> bool:
        return self.db.query(Role).filter(Role.nombre == nombre, Role.id != role_id).first() is not None
