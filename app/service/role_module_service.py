from typing import List, Optional

from fastapi import Depends

from app.dto.request.role_module import RoleModuleRequest, UpdateRoleModuleRequest
from app.dto.response.role_module import RoleModuleResponse
from app.exception import DuplicateResourceException, ForbiddenOperationException, ResourceNotFoundException
from app.model import RoleModule
from app.repository.module_repository import ModuleRepository
from app.repository.role_module_repository import RoleModuleRepository
from app.repository.role_repository import RoleRepository

ADMIN_MODULE = "Roles y módulos"


class RoleModuleService:

    def __init__(
        self,
        role_module_repository: RoleModuleRepository = Depends(),
        role_repository: RoleRepository = Depends(),
        module_repository: ModuleRepository = Depends(),
    ):
        self.role_module_repository = role_module_repository
        self.role_repository = role_repository
        self.module_repository = module_repository

    @staticmethod
    def to_response(rm: RoleModule) -> RoleModuleResponse:
        return RoleModuleResponse(
            id=rm.id, role_id=rm.role_id, role_name=rm.role.nombre, module_id=rm.module_id,
            module_name=rm.module.nombre, puede_ver=rm.puede_ver, puede_crear=rm.puede_crear,
            puede_editar=rm.puede_editar, puede_eliminar=rm.puede_eliminar, alcance=rm.alcance, estado=rm.estado,
        )

    def find_or_404(self, rm_id: int) -> RoleModule:
        rm = self.role_module_repository.find_active_by_id(rm_id)
        if rm is None:
            raise ResourceNotFoundException(f"Role-module permission with id {rm_id} not found")
        return rm

    @staticmethod
    def _protect_admin_lockout(rm: RoleModule) -> None:
        """Evita que el ADMIN pierda acceso a la administración de roles (quedaría bloqueado el sistema)."""
        if rm.role.nombre == "ADMIN" and rm.module.nombre == ADMIN_MODULE:
            raise ForbiddenOperationException("No se pueden modificar los permisos del ADMIN sobre Roles y módulos")

    @staticmethod
    def _apply_permissions(rm: RoleModule, request) -> None:
        rm.puede_ver, rm.puede_crear = request.puede_ver, request.puede_crear
        rm.puede_editar, rm.puede_eliminar = request.puede_editar, request.puede_eliminar
        rm.alcance = request.alcance

    def assign_module_to_role(self, request: RoleModuleRequest) -> RoleModuleResponse:
        role = self.role_repository.find_by_id(request.role_id)
        if role is None:
            raise ResourceNotFoundException(f"Role with id {request.role_id} not found")
        module = self.module_repository.find_by_id(request.module_id)
        if module is None:
            raise ResourceNotFoundException(f"Module with id {request.module_id} not found")

        existing = self.role_module_repository.find_by_role_and_module(role.id, module.id)
        if existing is not None and existing.estado:
            raise DuplicateResourceException("This module is already assigned to the role")

        if existing is not None:  # estaba desactivado: se reactiva con los nuevos permisos
            rm = existing
            rm.estado = True
        else:
            rm = RoleModule(role_id=role.id, module_id=module.id)
            self.role_module_repository.add(rm)

        self._apply_permissions(rm, request)
        self.role_module_repository.commit()
        self.role_module_repository.refresh(rm)
        return self.to_response(rm)

    def get_all_permissions(self, role_id: Optional[int] = None) -> List[RoleModuleResponse]:
        return [self.to_response(rm) for rm in self.role_module_repository.find_all_active(role_id)]

    def update_permissions(self, rm_id: int, request: UpdateRoleModuleRequest) -> RoleModuleResponse:
        rm = self.find_or_404(rm_id)
        self._protect_admin_lockout(rm)
        self._apply_permissions(rm, request)
        self.role_module_repository.commit()
        self.role_module_repository.refresh(rm)
        return self.to_response(rm)

    def remove_module_from_role(self, rm_id: int) -> RoleModuleResponse:
        rm = self.find_or_404(rm_id)
        self._protect_admin_lockout(rm)
        rm.estado = False
        self.role_module_repository.commit()
        self.role_module_repository.refresh(rm)
        return self.to_response(rm)
