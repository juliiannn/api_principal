from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import Access, require_permission
from app.dto.request.module import CreateModuleRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.module import ModuleResponse
from app.service.module_service import ModuleService

router = APIRouter(prefix="/modules", tags=["Modules"])

MODULE = "Roles y módulos"


@router.post("", response_model=ApiResponse[ModuleResponse], status_code=201)
def create_module(
    request: CreateModuleRequest, service: ModuleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(success=True, message="Module created successfully", data=service.create_module(request))


@router.get("", response_model=ApiResponse[List[ModuleResponse]])
def get_all_modules(
    include_inactive: bool = False, service: ModuleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(
        success=True, message="Modules retrieved successfully", data=service.get_all_modules(include_inactive)
    )


@router.get("/{module_id}", response_model=ApiResponse[ModuleResponse])
def get_module_by_id(
    module_id: int, service: ModuleService = Depends(), _: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(success=True, message="Module retrieved successfully", data=service.get_module_by_id(module_id))


@router.put("/{module_id}", response_model=ApiResponse[ModuleResponse])
def update_module(
    module_id: int, request: CreateModuleRequest, service: ModuleService = Depends(),
    _: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(
        success=True, message="Module updated successfully", data=service.update_module(module_id, request)
    )


@router.put("/{module_id}/deactivate", response_model=ApiResponse[ModuleResponse])
def deactivate_module(
    module_id: int, service: ModuleService = Depends(), _: Access = Depends(require_permission(MODULE, "eliminar")),
):
    return ApiResponse(
        success=True, message="Module deactivated successfully", data=service.deactivate_module(module_id)
    )


@router.put("/{module_id}/activate", response_model=ApiResponse[ModuleResponse])
def activate_module(
    module_id: int, service: ModuleService = Depends(), _: Access = Depends(require_permission(MODULE, "eliminar")),
):
    return ApiResponse(success=True, message="Module activated successfully", data=service.activate_module(module_id))
