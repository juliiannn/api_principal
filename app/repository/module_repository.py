from typing import List, Optional

from app.model import Module
from app.repository.base_repository import BaseRepository


class ModuleRepository(BaseRepository):

    def find_by_id(self, module_id: int, include_inactive: bool = False) -> Optional[Module]:
        q = self.db.query(Module).filter(Module.id == module_id)
        if not include_inactive:
            q = q.filter(Module.estado.is_(True))
        return q.first()

    def find_all(self, include_inactive: bool = False) -> List[Module]:
        q = self.db.query(Module)
        if not include_inactive:
            q = q.filter(Module.estado.is_(True))
        return q.all()

    def exists_by_name(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(Module).filter(Module.nombre == nombre)
        if exclude_id is not None:
            q = q.filter(Module.id != exclude_id)
        return q.first() is not None

    def exists_by_route(self, ruta: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(Module).filter(Module.ruta == ruta)
        if exclude_id is not None:
            q = q.filter(Module.id != exclude_id)
        return q.first() is not None
