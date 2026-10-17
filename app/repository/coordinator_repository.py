from typing import List, Optional

from app.model import Coordinator
from app.repository.base_repository import BaseRepository


class CoordinatorRepository(BaseRepository):

    def find_active_by_id(self, coordinator_id: int) -> Optional[Coordinator]:
        return self.db.query(Coordinator).filter(Coordinator.id == coordinator_id, Coordinator.estado.is_(True)).first()

    def find_all_active(self) -> List[Coordinator]:
        return self.db.query(Coordinator).filter(Coordinator.estado.is_(True)).all()

    def find_active_by_user_id(self, user_id: int) -> Optional[Coordinator]:
        return self.db.query(Coordinator).filter(Coordinator.user_id == user_id, Coordinator.estado.is_(True)).first()

    def exists_by_employee_code(self, employee_code: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(Coordinator).filter(Coordinator.employee_code == employee_code)
        if exclude_id is not None:
            q = q.filter(Coordinator.id != exclude_id)
        return q.first() is not None

    def count_active(self) -> int:
        return self.db.query(Coordinator).filter(Coordinator.estado.is_(True)).count()
