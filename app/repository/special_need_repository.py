from typing import List, Optional

from app.model import SpecialNeed
from app.repository.base_repository import BaseRepository


class SpecialNeedRepository(BaseRepository):

    def find_by_id(self, need_id: int, include_inactive: bool = False) -> Optional[SpecialNeed]:
        q = self.db.query(SpecialNeed).filter(SpecialNeed.id == need_id)
        if not include_inactive:
            q = q.filter(SpecialNeed.estado.is_(True))
        return q.first()

    def find_all(self, include_inactive: bool = False) -> List[SpecialNeed]:
        q = self.db.query(SpecialNeed)
        if not include_inactive:
            q = q.filter(SpecialNeed.estado.is_(True))
        return q.all()

    def exists_by_name_ignore_case(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(SpecialNeed).filter(SpecialNeed.nombre.ilike(nombre))
        if exclude_id is not None:
            q = q.filter(SpecialNeed.id != exclude_id)
        return q.first() is not None
