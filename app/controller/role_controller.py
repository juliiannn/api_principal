from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import Access, require_permission
from app.dto.request.role import CreateRoleRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.role import RoleResponse
from app.service.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])

MODULE = "Roles y módulos"


@router.post("", response_model=ApiResponse[RoleResponse], status_code=201)
def create_role(
    request: CreateRoleRequest, service: RoleService = Depends(), _: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(success=True, message="Role created successfully", data=service.create_role(request))


@router.get("", response_model=ApiResponse[List[RoleResponse]])
def get_all_roles(
    include_inactive: bool = False, service: RoleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(success=True, message="Roles retrieved successfully", data=service.get_all_roles(include_inactive))


@router.get("/{role_id}", response_model=ApiResponse[RoleResponse])
def get_role_by_id(role_id: int, service: RoleService = Depends(), _: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Role retrieved successfully", data=service.get_role_by_id(role_id))


@router.put("/{role_id}", response_model=ApiResponse[RoleResponse])
def update_role(
    role_id: int, request: CreateRoleRequest, service: RoleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(success=True, message="Role updated successfully", data=service.update_role(role_id, request))


@router.put("/{role_id}/deactivate", response_model=ApiResponse[RoleResponse])
def deactivate_role(
    role_id: int, service: RoleService = Depends(), _: Access = Depends(require_permission(MODULE, "eliminar")),
):
    return ApiResponse(success=True, message="Role deactivated successfully", data=service.deactivate_role(role_id))


@router.put("/{role_id}/activate", response_model=ApiResponse[RoleResponse])
def activate_role(
    role_id: int, service: RoleService = Depends(), _: Access = Depends(require_permission(MODULE, "eliminar")),
):
    return ApiResponse(success=True, message="Role activated successfully", data=service.activate_role(role_id))
