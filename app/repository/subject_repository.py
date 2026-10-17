from typing import List, Optional

from app.model import Subject
from app.repository.base_repository import BaseRepository


class SubjectRepository(BaseRepository):

    def find_by_id(self, subject_id: int, include_inactive: bool = False) -> Optional[Subject]:
        q = self.db.query(Subject).filter(Subject.id == subject_id)
        if not include_inactive:
            q = q.filter(Subject.estado.is_(True))
        return q.first()

    def find_all(self, include_inactive: bool = False) -> List[Subject]:
        q = self.db.query(Subject)
        if not include_inactive:
            q = q.filter(Subject.estado.is_(True))
        return q.all()

    def exists_by_name_ignore_case(self, name: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(Subject).filter(Subject.name.ilike(name))
        if exclude_id is not None:
            q = q.filter(Subject.id != exclude_id)
        return q.first() is not None

    def count_active(self) -> int:
        return self.db.query(Subject).filter(Subject.estado.is_(True)).count()
