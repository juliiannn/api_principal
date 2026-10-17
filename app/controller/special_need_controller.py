from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import Access, require_permission
from app.dto.request.special_need import CreateSpecialNeedRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.special_need import SpecialNeedResponse
from app.service.special_need_service import SpecialNeedService

router = APIRouter(prefix="/special-needs", tags=["SpecialNeeds"])

MODULE = "Necesidades educativas"


@router.post("", response_model=ApiResponse[SpecialNeedResponse], status_code=201)
def create_special_need(
    request: CreateSpecialNeedRequest, service: SpecialNeedService = Depends(),
    _: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(
        success=True, message="Special need created successfully", data=service.create_special_need(request)
    )


@router.get("", response_model=ApiResponse[List[SpecialNeedResponse]])
def get_all_special_needs(
    include_inactive: bool = False, service: SpecialNeedService = Depends(),
    _: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(
        success=True, message="Special needs retrieved successfully",
        data=service.get_all_special_needs(include_inactive),
    )


@router.put("/{need_id}", response_model=ApiResponse[SpecialNeedResponse])
def update_special_need(
    need_id: int, request: CreateSpecialNeedRequest, service: SpecialNeedService = Depends(),
    _: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(
        success=True, message="Special need updated successfully", data=service.update_special_need(need_id, request)
    )


@router.put("/{need_id}/deactivate", response_model=ApiResponse[SpecialNeedResponse])
def deactivate_special_need(
    need_id: int, service: SpecialNeedService = Depends(), _: Access = Depends(require_permission(MODULE, "eliminar")),
):
    return ApiResponse(
        success=True, message="Special need deactivated successfully", data=service.deactivate_special_need(need_id)
    )


@router.put("/{need_id}/activate", response_model=ApiResponse[SpecialNeedResponse])
def activate_special_need(
    need_id: int, service: SpecialNeedService = Depends(), _: Access = Depends(require_permission(MODULE, "eliminar")),
):
    return ApiResponse(
        success=True, message="Special need activated successfully", data=service.activate_special_need(need_id)
    )
