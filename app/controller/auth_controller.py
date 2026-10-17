from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_user
from app.dto.request.auth import ChangePasswordRequest, LoginRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.auth import TokenResponse
from app.dto.response.role_module import MyPermissionResponse
from app.model import User
from app.service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(request: LoginRequest, service: AuthService = Depends()):
    return ApiResponse(success=True, message="Login successful", data=service.login(request))


@router.put("/change-password", response_model=ApiResponse[None])
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(),
):
    service.change_password(current_user, request)
    return ApiResponse(success=True, message="Password changed successfully", data=None)


@router.get("/me/permissions", response_model=ApiResponse[List[MyPermissionResponse]])
def get_my_permissions(current_user: User = Depends(get_current_user), service: AuthService = Depends()):
    """Módulos y permisos del usuario autenticado (sirve para armar el menú del frontend)."""
    return ApiResponse(
        success=True, message="Permissions retrieved successfully", data=service.get_my_permissions(current_user)
    )
