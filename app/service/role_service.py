from typing import List

from fastapi import Depends

from app.dto.request.role import CreateRoleRequest
from app.exception import DuplicateResourceException, InvalidRequestException, ResourceNotFoundException
from app.model import Role, UserRole
from app.repository.role_repository import RoleRepository
from app.repository.user_repository import UserRepository

SYSTEM_ROLES = {r.value for r in UserRole}


class RoleService:

    def __init__(
        self,
        role_repository: RoleRepository = Depends(),
        user_repository: UserRepository = Depends(),
    ):
        self.role_repository = role_repository
        self.user_repository = user_repository

    def find_or_404(self, role_id: int, include_inactive: bool = False) -> Role:
        role = self.role_repository.find_by_id(role_id, include_inactive)
        if role is None:
            raise ResourceNotFoundException(f"Role with id {role_id} not found")
        return role

    def create_role(self, request: CreateRoleRequest) -> Role:
        nombre = request.nombre.strip().upper()
        if self.role_repository.exists_by_name(nombre):
            raise DuplicateResourceException("Role already exists")
        return self.role_repository.save(Role(nombre=nombre, descripcion=request.descripcion))

    def get_all_roles(self, include_inactive: bool = False) -> List[Role]:
        return self.role_repository.find_all(include_inactive)

    def get_role_by_id(self, role_id: int) -> Role:
        return self.find_or_404(role_id)

    def update_role(self, role_id: int, request: CreateRoleRequest) -> Role:
        role = self.find_or_404(role_id)
        nombre = request.nombre.strip().upper()
        if role.nombre in SYSTEM_ROLES and nombre != role.nombre:
            raise InvalidRequestException("Los roles del sistema no se pueden renombrar")
        if self.role_repository.exists_by_name_and_id_not(nombre, role_id):
            raise DuplicateResourceException("Role already exists")
        role.nombre = nombre
        role.descripcion = request.descripcion
        self.role_repository.commit()
        return self.role_repository.refresh(role)

    def deactivate_role(self, role_id: int) -> Role:
        role = self.find_or_404(role_id)
        if role.nombre in SYSTEM_ROLES:
            raise InvalidRequestException("Los roles del sistema no se pueden desactivar")
        if self.user_repository.exists_active_by_role_id(role.id):
            raise InvalidRequestException("No se puede desactivar un rol que tiene usuarios activos")
        role.estado = False
        self.role_repository.commit()
        return self.role_repository.refresh(role)

    def activate_role(self, role_id: int) -> Role:
        role = self.find_or_404(role_id, include_inactive=True)
        role.estado = True
        self.role_repository.commit()
        return self.role_repository.refresh(role)
