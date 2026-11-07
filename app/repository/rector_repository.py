from typing import List, Optional

from app.model import Rector, User
from app.repository.base_repository import BaseRepository


class RectorRepository(BaseRepository):

    def find_active_by_id(self, rector_id: int) -> Optional[Rector]:
        return self.db.query(Rector).filter(Rector.id == rector_id, Rector.estado.is_(True)).first()

    def find_all_active(self) -> List[Rector]:
        return self.db.query(Rector).filter(Rector.estado.is_(True)).all()

    def find_active_by_user_id(self, user_id: int) -> Optional[Rector]:
        return self.db.query(Rector).filter(Rector.user_id == user_id, Rector.estado.is_(True)).first()

    def exists_by_employee_code(self, employee_code: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(Rector).filter(Rector.employee_code == employee_code)
        if exclude_id is not None:
            q = q.filter(Rector.id != exclude_id)
        return q.first() is not None

    def count_active_enabled(self) -> int:
        """Rectores activos cuyo usuario está habilitado."""
        return (
            self.db.query(Rector).join(User, Rector.user_id == User.id)
            .filter(User.enabled == True, Rector.estado.is_(True)).count()  # noqa: E712
        )

