from typing import List, Optional

from app.model import Period, PiarGoal, PiarProgress
from app.repository.base_repository import BaseRepository


class PiarProgressRepository(BaseRepository):

    def find_active_by_id(self, progress_id: int) -> Optional[PiarProgress]:
        return self.db.query(PiarProgress).filter(
            PiarProgress.id == progress_id, PiarProgress.estado.is_(True)
        ).first()

    def exists_by_goal_and_period(self, goal_id: int, period: Period) -> bool:
        return self.db.query(PiarProgress).filter(
            PiarProgress.piar_goal_id == goal_id, PiarProgress.period == period
        ).first() is not None

    def find_active_by_piar_ordered_by_period(self, piar_id: int) -> List[PiarProgress]:
        return (
            self.db.query(PiarProgress).join(PiarGoal, PiarProgress.piar_goal_id == PiarGoal.id)
            .filter(PiarGoal.piar_id == piar_id, PiarGoal.estado.is_(True), PiarProgress.estado.is_(True))
            .order_by(PiarProgress.period).all()
        )
