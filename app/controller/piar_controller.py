from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import Access, get_current_teacher, require_permission
from app.dto.request.piar import (
    CreatePiarAdjustmentRequest, CreatePiarGoalRequest, CreatePiarProgressRequest, CreatePiarRequest,
    PiarNeedInput, UpdatePiarProgressRequest, UpdatePiarRequest,
)
from app.dto.response.api_response import ApiResponse
from app.dto.response.piar import PiarAdjustmentResponse, PiarGoalResponse, PiarProgressResponse, PiarResponse
from app.model import Teacher
from app.service.piar_service import PiarService

router = APIRouter(prefix="/piars", tags=["PIAR"])

MODULE = "PIAR"


# ===== Plan =====

@router.post("", response_model=ApiResponse[PiarResponse], status_code=201)
def create_piar(
    request: CreatePiarRequest, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(success=True, message="PIAR created successfully", data=service.create_piar(request, access))


@router.get("/me", response_model=ApiResponse[List[PiarResponse]])
def get_my_piars(service: PiarService = Depends(), access: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="PIAR retrieved successfully", data=service.get_my_piars(access))


@router.get("/student/{student_id}", response_model=ApiResponse[List[PiarResponse]])
def get_piars_by_student(
    student_id: int, service: PiarService = Depends(), access: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(
        success=True, message="PIAR retrieved successfully", data=service.get_piars_by_student(student_id, access)
    )


# ===== Metas, ajustes y avance (rutas fijas antes de /{piar_id}) =====

@router.post("/goals", response_model=ApiResponse[PiarGoalResponse], status_code=201)
def create_goal(
    request: CreatePiarGoalRequest, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(success=True, message="Goal created successfully", data=service.create_goal(request, access))


@router.post("/adjustments", response_model=ApiResponse[PiarAdjustmentResponse], status_code=201)
def create_adjustment(
    request: CreatePiarAdjustmentRequest, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(
        success=True, message="Adjustment created successfully", data=service.create_adjustment(request, access)
    )


@router.post("/progress", response_model=ApiResponse[PiarProgressResponse], status_code=201)
def register_progress(
    request: CreatePiarProgressRequest, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "crear")),
    teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Progress registered successfully",
        data=service.register_progress(request, access, teacher),
    )


@router.put("/progress/{progress_id}", response_model=ApiResponse[PiarProgressResponse])
def update_progress(
    progress_id: int, request: UpdatePiarProgressRequest, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(
        success=True, message="Progress updated successfully",
        data=service.update_progress(progress_id, request, access),
    )


# ===== Detalle del plan =====

@router.get("/{piar_id}", response_model=ApiResponse[PiarResponse])
def get_piar_by_id(
    piar_id: int, service: PiarService = Depends(), access: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(success=True, message="PIAR retrieved successfully", data=service.get_piar_by_id(piar_id, access))


@router.put("/{piar_id}", response_model=ApiResponse[PiarResponse])
def update_piar(
    piar_id: int, request: UpdatePiarRequest, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(
        success=True, message="PIAR updated successfully", data=service.update_piar(piar_id, request, access)
    )


@router.get("/{piar_id}/progress", response_model=ApiResponse[List[PiarProgressResponse]])
def get_piar_progress(
    piar_id: int, service: PiarService = Depends(), access: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(
        success=True, message="Progress retrieved successfully", data=service.get_piar_progress(piar_id, access)
    )


@router.post("/{piar_id}/needs", response_model=ApiResponse[PiarResponse], status_code=201)
def add_need(
    piar_id: int, request: PiarNeedInput, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "crear")),
):
    return ApiResponse(
        success=True, message="Need added successfully", data=service.add_need(piar_id, request, access)
    )


@router.put("/{piar_id}/needs/{special_need_id}/deactivate", response_model=ApiResponse[PiarResponse])
def remove_need(
    piar_id: int, special_need_id: int, service: PiarService = Depends(),
    access: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(
        success=True, message="Need removed successfully", data=service.remove_need(piar_id, special_need_id, access)
    )
