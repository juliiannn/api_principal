from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.request.user import CreateUserRequest, UpdateUserRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.user import UserResponse
from app.model import User
from app.service.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=ApiResponse[UserResponse], status_code=201)
def create_user(request: CreateUserRequest, service: UserService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="Admin user created successfully", data=service.create_user(request))


@router.get("", response_model=ApiResponse[List[UserResponse]])
def get_all_users(service: UserService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="Users retrieved successfully", data=service.get_all_users())


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
def get_user_by_id(user_id: int, service: UserService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="User retrieved successfully", data=service.get_user_by_id(user_id))


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
def update_user(
    user_id: int, request: UpdateUserRequest,
    service: UserService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(success=True, message="User updated successfully", data=service.update_user(user_id, request))


@router.put("/{user_id}/activate", response_model=ApiResponse[UserResponse])
def activate_user(user_id: int, service: UserService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="User activated successfully", data=service.set_enabled(user_id, True))


@router.put("/{user_id}/deactivate", response_model=ApiResponse[UserResponse])
def deactivate_user(user_id: int, service: UserService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="User deactivated successfully", data=service.set_enabled(user_id, False))


@router.put("/{user_id}/reset-password", response_model=ApiResponse[UserResponse])
def reset_password(user_id: int, service: UserService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="Password reset successfully", data=service.reset_password(user_id))
