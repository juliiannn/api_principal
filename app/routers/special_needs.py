from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import Access, require_permission
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import SpecialNeed
from app.schemas import ApiResponse, CreateSpecialNeedRequest, SpecialNeedResponse

router = APIRouter(prefix="/special-needs", tags=["SpecialNeeds"])

MODULE = "Necesidades educativas"


def find_or_404(db: Session, need_id: int, include_inactive: bool = False) -> SpecialNeed:
    q = db.query(SpecialNeed).filter(SpecialNeed.id == need_id)
    if not include_inactive:
        q = q.filter(SpecialNeed.estado.is_(True))
    need = q.first()
    if need is None:
        raise ResourceNotFoundException(f"Special need with id {need_id} not found")
    return need


@router.post("", response_model=ApiResponse[SpecialNeedResponse], status_code=201)
def create_special_need(request: CreateSpecialNeedRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "crear"))):
    nombre = request.nombre.strip()
    if db.query(SpecialNeed).filter(SpecialNeed.nombre.ilike(nombre)).first():
        raise DuplicateResourceException("Special need already exists")
    need = SpecialNeed(nombre=nombre, descripcion=request.descripcion)
    db.add(need)
    db.commit()
    db.refresh(need)
    return ApiResponse(success=True, message="Special need created successfully", data=need)


@router.get("", response_model=ApiResponse[List[SpecialNeedResponse]])
def get_all_special_needs(include_inactive: bool = False, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "ver"))):
    q = db.query(SpecialNeed)
    if not include_inactive:
        q = q.filter(SpecialNeed.estado.is_(True))
    return ApiResponse(success=True, message="Special needs retrieved successfully", data=q.all())


@router.put("/{need_id}", response_model=ApiResponse[SpecialNeedResponse])
def update_special_need(need_id: int, request: CreateSpecialNeedRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "editar"))):
    need = find_or_404(db, need_id)
    nombre = request.nombre.strip()
    if db.query(SpecialNeed).filter(SpecialNeed.nombre.ilike(nombre), SpecialNeed.id != need_id).first():
        raise DuplicateResourceException("Special need already exists")
    need.nombre, need.descripcion = nombre, request.descripcion
    db.commit()
    db.refresh(need)
    return ApiResponse(success=True, message="Special need updated successfully", data=need)


@router.put("/{need_id}/deactivate", response_model=ApiResponse[SpecialNeedResponse])
def deactivate_special_need(need_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "eliminar"))):
    need = find_or_404(db, need_id)
    need.estado = False
    db.commit()
    db.refresh(need)
    return ApiResponse(success=True, message="Special need deactivated successfully", data=need)


@router.put("/{need_id}/activate", response_model=ApiResponse[SpecialNeedResponse])
def activate_special_need(need_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "eliminar"))):
    need = find_or_404(db, need_id, include_inactive=True)
    need.estado = True
    db.commit()
    db.refresh(need)
    return ApiResponse(success=True, message="Special need activated successfully", data=need)
