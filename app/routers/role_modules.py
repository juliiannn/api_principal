from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import Access, require_permission
from app.exceptions import DuplicateResourceException, ForbiddenOperationException, ResourceNotFoundException
from app.models import Module, Role, RoleModule
from app.schemas import ApiResponse, RoleModuleRequest, RoleModuleResponse, UpdateRoleModuleRequest

router = APIRouter(prefix="/role-modules", tags=["RoleModules"])

MODULE = "Roles y módulos"


def to_response(rm: RoleModule) -> RoleModuleResponse:
    return RoleModuleResponse(
        id=rm.id, role_id=rm.role_id, role_name=rm.role.nombre, module_id=rm.module_id, module_name=rm.module.nombre,
        puede_ver=rm.puede_ver, puede_crear=rm.puede_crear, puede_editar=rm.puede_editar,
        puede_eliminar=rm.puede_eliminar, alcance=rm.alcance, estado=rm.estado,
    )


def find_or_404(db: Session, rm_id: int) -> RoleModule:
    rm = db.query(RoleModule).filter(RoleModule.id == rm_id, RoleModule.estado.is_(True)).first()
    if rm is None:
        raise ResourceNotFoundException(f"Role-module permission with id {rm_id} not found")
    return rm


def protect_admin_lockout(rm: RoleModule):
    """Evita que el ADMIN pierda acceso a la administración de roles (quedaría bloqueado el sistema)."""
    if rm.role.nombre == "ADMIN" and rm.module.nombre == MODULE:
        raise ForbiddenOperationException("No se pueden modificar los permisos del ADMIN sobre Roles y módulos")


@router.post("", response_model=ApiResponse[RoleModuleResponse], status_code=201)
def assign_module_to_role(request: RoleModuleRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "crear"))):
    role = db.query(Role).filter(Role.id == request.role_id, Role.estado.is_(True)).first()
    if role is None:
        raise ResourceNotFoundException(f"Role with id {request.role_id} not found")
    module = db.query(Module).filter(Module.id == request.module_id, Module.estado.is_(True)).first()
    if module is None:
        raise ResourceNotFoundException(f"Module with id {request.module_id} not found")

    existing = db.query(RoleModule).filter(RoleModule.role_id == role.id, RoleModule.module_id == module.id).first()
    if existing is not None and existing.estado:
        raise DuplicateResourceException("This module is already assigned to the role")

    if existing is not None:  # estaba desactivado: se reactiva con los nuevos permisos
        rm = existing
        rm.estado = True
    else:
        rm = RoleModule(role_id=role.id, module_id=module.id)
        db.add(rm)

    rm.puede_ver, rm.puede_crear = request.puede_ver, request.puede_crear
    rm.puede_editar, rm.puede_eliminar = request.puede_editar, request.puede_eliminar
    rm.alcance = request.alcance
    db.commit()
    db.refresh(rm)
    return ApiResponse(success=True, message="Module assigned to role successfully", data=to_response(rm))


@router.get("", response_model=ApiResponse[List[RoleModuleResponse]])
def get_all_permissions(role_id: Optional[int] = None, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "ver"))):
    q = db.query(RoleModule).filter(RoleModule.estado.is_(True))
    if role_id is not None:
        q = q.filter(RoleModule.role_id == role_id)
    return ApiResponse(success=True, message="Permissions retrieved successfully", data=[to_response(rm) for rm in q.all()])


@router.put("/{rm_id}", response_model=ApiResponse[RoleModuleResponse])
def update_permissions(rm_id: int, request: UpdateRoleModuleRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "editar"))):
    rm = find_or_404(db, rm_id)
    protect_admin_lockout(rm)
    rm.puede_ver, rm.puede_crear = request.puede_ver, request.puede_crear
    rm.puede_editar, rm.puede_eliminar = request.puede_editar, request.puede_eliminar
    rm.alcance = request.alcance
    db.commit()
    db.refresh(rm)
    return ApiResponse(success=True, message="Permissions updated successfully", data=to_response(rm))


@router.put("/{rm_id}/deactivate", response_model=ApiResponse[RoleModuleResponse])
def remove_module_from_role(rm_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "eliminar"))):
    rm = find_or_404(db, rm_id)
    protect_admin_lockout(rm)
    rm.estado = False
    db.commit()
    db.refresh(rm)
    return ApiResponse(success=True, message="Module removed from role successfully", data=to_response(rm))
