"""Autenticación y autorización por petición (equivale a JwtAuthenticationFilter + @PreAuthorize)."""
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.config.access import Access
from app.config.security_config import bearer_scheme
from app.model import Student, Teacher, User
from app.repository.role_module_repository import RoleModuleRepository
from app.repository.user_repository import UserRepository
from app.service.current_user_service import CurrentUserService
from app.service.jwt_service import JwtService

Action = Literal["ver", "crear", "editar", "eliminar"]
_ACTION_COLUMN = {
    "ver": "puede_ver",
    "crear": "puede_crear",
    "editar": "puede_editar",
    "eliminar": "puede_eliminar",
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    jwt_service: JwtService = Depends(),
    user_repository: UserRepository = Depends(),
) -> User:
    payload = jwt_service.decode_access_token(credentials.credentials)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    user = user_repository.find_active_by_email(payload.get("sub"))

    if user is None or not user.enabled or not user.role_ref.estado:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido o inactivo")

    return user


def require_role(*allowed_roles: str):
    """Restringe el endpoint por nombre de rol (equivale a hasRole(...))."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_ref.nombre not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos suficientes")
        return current_user

    return role_checker


def require_permission(module_name: str, action: Action):
    """Uso: access: Access = Depends(require_permission("Notas", "crear")).
    Luego access.scope indica ALL / ASSIGNED / OWN para filtrar los datos en el endpoint."""
    def checker(
        current_user: User = Depends(get_current_user),
        role_module_repository: RoleModuleRepository = Depends(),
    ) -> Access:
        perm = role_module_repository.find_permission(current_user.role_id, module_name)
        if perm is None or not getattr(perm, _ACTION_COLUMN[action]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos suficientes")
        return Access(user=current_user, scope=perm.alcance)

    return checker


def get_current_teacher(
    current_user: User = Depends(get_current_user),
    current_user_service: CurrentUserService = Depends(),
) -> Teacher:
    teacher = current_user_service.find_teacher(current_user)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No teacher profile found")
    return teacher


def get_current_student(
    current_user: User = Depends(get_current_user),
    current_user_service: CurrentUserService = Depends(),
) -> Student:
    student = current_user_service.find_student(current_user)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student profile found")
    return student
