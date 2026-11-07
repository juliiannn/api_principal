from typing import List, Optional

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import Access, require_permission
from app.dto.request.role_module import RoleModuleRequest, UpdateRoleModuleRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.role_module import RoleModuleResponse
from app.service.role_module_service import RoleModuleService

router = APIRouter(prefix="/role-modules", tags=["RoleModules"])

MODULE = "Roles y módulos"


@router.post("", response_model=ApiResponse[RoleModuleResponse], status_code=201)
def assign_module_to_role(
    request: RoleModuleRequest, service: RoleModuleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(
        success=True, message="Module assigned to role successfully", data=service.assign_module_to_role(request)
    )


@router.get("", response_model=ApiResponse[List[RoleModuleResponse]])
def get_all_permissions(
    role_id: Optional[int] = None, service: RoleModuleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(
        success=True, message="Permissions retrieved successfully", data=service.get_all_permissions(role_id)
    )


@router.put("/{rm_id}", response_model=ApiResponse[RoleModuleResponse])
def update_permissions(
    rm_id: int, request: UpdateRoleModuleRequest, service: RoleModuleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(
        success=True, message="Permissions updated successfully", data=service.update_permissions(rm_id, request)
    )


@router.put("/{rm_id}/deactivate", response_model=ApiResponse[RoleModuleResponse])
def remove_module_from_role(
    rm_id: int, service: RoleModuleService = Depends(), _: Access = Depends(require_permission(MODULE, "eliminar")),
):
    return ApiResponse(
        success=True, message="Module removed from role successfully", data=service.remove_module_from_role(rm_id)
    )
