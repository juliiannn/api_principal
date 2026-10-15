from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import Access, require_permission
from app.exceptions import DuplicateResourceException, InvalidRequestException, ResourceNotFoundException
from app.models import Role, User, UserRole
from app.schemas import ApiResponse, CreateRoleRequest, RoleResponse

router = APIRouter(prefix="/roles", tags=["Roles"])

MODULE = "Roles y módulos"
SYSTEM_ROLES = {r.value for r in UserRole}


def find_or_404(db: Session, role_id: int, include_inactive: bool = False) -> Role:
    q = db.query(Role).filter(Role.id == role_id)
    if not include_inactive:
        q = q.filter(Role.estado.is_(True))
    role = q.first()
    if role is None:
        raise ResourceNotFoundException(f"Role with id {role_id} not found")
    return role


@router.post("", response_model=ApiResponse[RoleResponse], status_code=201)
def create_role(request: CreateRoleRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "crear"))):
    nombre = request.nombre.strip().upper()
    if db.query(Role).filter(Role.nombre == nombre).first():
        raise DuplicateResourceException("Role already exists")
    role = Role(nombre=nombre, descripcion=request.descripcion)
    db.add(role)
    db.commit()
    db.refresh(role)
    return ApiResponse(success=True, message="Role created successfully", data=role)


@router.get("", response_model=ApiResponse[List[RoleResponse]])
def get_all_roles(include_inactive: bool = False, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "ver"))):
    q = db.query(Role)
    if not include_inactive:
        q = q.filter(Role.estado.is_(True))
    return ApiResponse(success=True, message="Roles retrieved successfully", data=q.all())


@router.get("/{role_id}", response_model=ApiResponse[RoleResponse])
def get_role_by_id(role_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Role retrieved successfully", data=find_or_404(db, role_id))


@router.put("/{role_id}", response_model=ApiResponse[RoleResponse])
def update_role(role_id: int, request: CreateRoleRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "editar"))):
    role = find_or_404(db, role_id)
    nombre = request.nombre.strip().upper()
    if role.nombre in SYSTEM_ROLES and nombre != role.nombre:
        raise InvalidRequestException("Los roles del sistema no se pueden renombrar")
    if db.query(Role).filter(Role.nombre == nombre, Role.id != role_id).first():
        raise DuplicateResourceException("Role already exists")
    role.nombre = nombre
    role.descripcion = request.descripcion
    db.commit()
    db.refresh(role)
    return ApiResponse(success=True, message="Role updated successfully", data=role)


@router.put("/{role_id}/deactivate", response_model=ApiResponse[RoleResponse])
def deactivate_role(role_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "eliminar"))):
    role = find_or_404(db, role_id)
    if role.nombre in SYSTEM_ROLES:
        raise InvalidRequestException("Los roles del sistema no se pueden desactivar")
    if db.query(User).filter(User.role_id == role.id, User.estado.is_(True)).first():
        raise InvalidRequestException("No se puede desactivar un rol que tiene usuarios activos")
    role.estado = False
    db.commit()
    db.refresh(role)
    return ApiResponse(success=True, message="Role deactivated successfully", data=role)


@router.put("/{role_id}/activate", response_model=ApiResponse[RoleResponse])
def activate_role(role_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "eliminar"))):
    role = find_or_404(db, role_id, include_inactive=True)
    role.estado = True
    db.commit()
    db.refresh(role)
    return ApiResponse(success=True, message="Role activated successfully", data=role)
