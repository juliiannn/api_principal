from typing import Optional

from app.model import PiarGoal
from app.repository.base_repository import BaseRepository


class PiarGoalRepository(BaseRepository):

    def find_active_by_id(self, goal_id: int) -> Optional[PiarGoal]:
        return self.db.query(PiarGoal).filter(PiarGoal.id == goal_id, PiarGoal.estado.is_(True)).first()
