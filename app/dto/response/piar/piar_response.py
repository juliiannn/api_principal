from datetime import date, datetime
from typing import Optional, List
from app.dto.camel_model import CamelModel
from app.dto.response.piar.piar_adjustment_response import PiarAdjustmentResponse
from app.dto.response.piar.piar_goal_response import PiarGoalResponse
from app.dto.response.piar.piar_need_response import PiarNeedResponse


class PiarResponse(CamelModel):
    id: int
    student_id: int
    student_name: str
    school_year: int
    fecha_inicio: date
    fecha_fin: Optional[date]
    observaciones: Optional[str]
    consentimiento_acudiente: bool
    needs: List[PiarNeedResponse] = []
    goals: List[PiarGoalResponse] = []
    adjustments: List[PiarAdjustmentResponse] = []
    estado: bool
    creado: Optional[datetime] = None
    actualizado: Optional[datetime] = None
