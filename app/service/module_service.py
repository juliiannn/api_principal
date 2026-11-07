from typing import List, Optional

from fastapi import Depends

from app.dto.request.module import CreateModuleRequest
from app.exception import DuplicateResourceException, ResourceNotFoundException
from app.model import Module
from app.repository.module_repository import ModuleRepository


class ModuleService:

    def __init__(self, module_repository: ModuleRepository = Depends()):
        self.module_repository = module_repository

    def find_or_404(self, module_id: int, include_inactive: bool = False) -> Module:
        module = self.module_repository.find_by_id(module_id, include_inactive)
        if module is None:
            raise ResourceNotFoundException(f"Module with id {module_id} not found")
        return module

    def _check_duplicate(self, nombre: str, ruta: str, exclude_id: Optional[int] = None) -> None:
        if self.module_repository.exists_by_name(nombre, exclude_id):
            raise DuplicateResourceException("Module name already exists")
        if self.module_repository.exists_by_route(ruta, exclude_id):
            raise DuplicateResourceException("Module route already exists")

    def create_module(self, request: CreateModuleRequest) -> Module:
        nombre, ruta = request.nombre.strip(), request.ruta.strip()
        self._check_duplicate(nombre, ruta)
        return self.module_repository.save(Module(nombre=nombre, ruta=ruta, descripcion=request.descripcion))

    def get_all_modules(self, include_inactive: bool = False) -> List[Module]:
        return self.module_repository.find_all(include_inactive)

    def get_module_by_id(self, module_id: int) -> Module:
        return self.find_or_404(module_id)

    def update_module(self, module_id: int, request: CreateModuleRequest) -> Module:
        module = self.find_or_404(module_id)
        nombre, ruta = request.nombre.strip(), request.ruta.strip()
        self._check_duplicate(nombre, ruta, exclude_id=module_id)
        module.nombre, module.ruta, module.descripcion = nombre, ruta, request.descripcion
        self.module_repository.commit()
        return self.module_repository.refresh(module)

    def deactivate_module(self, module_id: int) -> Module:
        module = self.find_or_404(module_id)
        module.estado = False
        self.module_repository.commit()
        return self.module_repository.refresh(module)

    def activate_module(self, module_id: int) -> Module:
        module = self.find_or_404(module_id, include_inactive=True)
        module.estado = True
        self.module_repository.commit()
        return self.module_repository.refresh(module)
