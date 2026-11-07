from typing import List

from fastapi import Depends

from app.config.security_config import hash_password, verify_password
from app.dto.request.auth import ChangePasswordRequest, LoginRequest
from app.dto.response.auth import TokenResponse
from app.dto.response.role_module import MyPermissionResponse
from app.exception import InvalidCredentialsException, InvalidRequestException
from app.model import User
from app.repository.user_repository import UserRepository
from app.service.current_user_service import CurrentUserService
from app.service.jwt_service import JwtService


class AuthService:

    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        jwt_service: JwtService = Depends(),
        current_user_service: CurrentUserService = Depends(),
    ):
        self.user_repository = user_repository
        self.jwt_service = jwt_service
        self.current_user_service = current_user_service

    def login(self, request: LoginRequest) -> TokenResponse:
        email = request.email.strip().lower()
        user = self.user_repository.find_active_by_email(email)

        if (
            user is None or not user.enabled or not user.role_ref.estado
            or not verify_password(request.password, user.password)
        ):
            raise InvalidCredentialsException("Invalid credentials")

        token = self.jwt_service.create_access_token(email=user.email, role=user.role.value)

        return TokenResponse(
            access_token=token, expires_in=self.jwt_service.expiration_minutes * 60,
            must_change_password=user.must_change_password, role=user.role,
        )

    def change_password(self, current_user: User, request: ChangePasswordRequest) -> None:
        if not verify_password(request.current_password, current_user.password):
            raise InvalidCredentialsException("Current password is incorrect")
        if verify_password(request.new_password, current_user.password):
            raise InvalidRequestException("New password must be different from the current password")

        current_user.password = hash_password(request.new_password)
        current_user.must_change_password = False
        self.user_repository.commit()

    def get_my_permissions(self, current_user: User) -> List[MyPermissionResponse]:
        """Módulos y permisos del usuario autenticado (sirve para armar el menú del frontend)."""
        permissions = self.current_user_service.get_user_permissions(current_user)
        return [
            MyPermissionResponse(
                modulo=p.module.nombre, ruta=p.module.ruta, puede_ver=p.puede_ver, puede_crear=p.puede_crear,
                puede_editar=p.puede_editar, puede_eliminar=p.puede_eliminar, alcance=p.alcance,
            )
            for p in permissions
        ]
