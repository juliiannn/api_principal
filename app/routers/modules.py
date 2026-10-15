from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import Access, require_permission
from app.exceptions import DuplicateResourceException, ResourceNotFoundException
from app.models import Module
from app.schemas import ApiResponse, CreateModuleRequest, ModuleResponse

router = APIRouter(prefix="/modules", tags=["Modules"])

MODULE = "Roles y módulos"


def find_or_404(db: Session, module_id: int, include_inactive: bool = False) -> Module:
    q = db.query(Module).filter(Module.id == module_id)
    if not include_inactive:
        q = q.filter(Module.estado.is_(True))
    module = q.first()
    if module is None:
        raise ResourceNotFoundException(f"Module with id {module_id} not found")
    return module


def check_duplicate(db: Session, nombre: str, ruta: str, exclude_id: int = None):
    for column, value, label in ((Module.nombre, nombre, "name"), (Module.ruta, ruta, "route")):
        q = db.query(Module).filter(column == value)
        if exclude_id is not None:
            q = q.filter(Module.id != exclude_id)
        if q.first():
            raise DuplicateResourceException(f"Module {label} already exists")


@router.post("", response_model=ApiResponse[ModuleResponse], status_code=201)
def create_module(request: CreateModuleRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "crear"))):
    nombre, ruta = request.nombre.strip(), request.ruta.strip()
    check_duplicate(db, nombre, ruta)
    module = Module(nombre=nombre, ruta=ruta, descripcion=request.descripcion)
    db.add(module)
    db.commit()
    db.refresh(module)
    return ApiResponse(success=True, message="Module created successfully", data=module)


@router.get("", response_model=ApiResponse[List[ModuleResponse]])
def get_all_modules(include_inactive: bool = False, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "ver"))):
    q = db.query(Module)
    if not include_inactive:
        q = q.filter(Module.estado.is_(True))
    return ApiResponse(success=True, message="Modules retrieved successfully", data=q.all())


@router.get("/{module_id}", response_model=ApiResponse[ModuleResponse])
def get_module_by_id(module_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Module retrieved successfully", data=find_or_404(db, module_id))


@router.put("/{module_id}", response_model=ApiResponse[ModuleResponse])
def update_module(module_id: int, request: CreateModuleRequest, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "editar"))):
    module = find_or_404(db, module_id)
    nombre, ruta = request.nombre.strip(), request.ruta.strip()
    check_duplicate(db, nombre, ruta, exclude_id=module_id)
    module.nombre, module.ruta, module.descripcion = nombre, ruta, request.descripcion
    db.commit()
    db.refresh(module)
    return ApiResponse(success=True, message="Module updated successfully", data=module)


@router.put("/{module_id}/deactivate", response_model=ApiResponse[ModuleResponse])
def deactivate_module(module_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "eliminar"))):
    module = find_or_404(db, module_id)
    module.estado = False
    db.commit()
    db.refresh(module)
    return ApiResponse(success=True, message="Module deactivated successfully", data=module)


@router.put("/{module_id}/activate", response_model=ApiResponse[ModuleResponse])
def activate_module(module_id: int, db: Session = Depends(get_db), _: Access = Depends(require_permission(MODULE, "eliminar"))):
    module = find_or_404(db, module_id, include_inactive=True)
    module.estado = True
    db.commit()
    db.refresh(module)
    return ApiResponse(success=True, message="Module activated successfully", data=module)
