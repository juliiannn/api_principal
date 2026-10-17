from datetime import date
from typing import Optional, List
from pydantic import BaseModel
from app.dto.request.piar.piar_need_input import PiarNeedInput


class CreatePiarRequest(BaseModel):
    student_id: int
    school_year: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    observaciones: Optional[str] = None
    consentimiento_acudiente: bool = False
    needs: List[PiarNeedInput] = []
