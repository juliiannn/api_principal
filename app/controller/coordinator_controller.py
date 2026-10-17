from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.request.coordinator import CreateCoordinatorRequest, UpdateCoordinatorRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.coordinator import CoordinatorResponse
from app.model import User
from app.service.coordinator_service import CoordinatorService

router = APIRouter(prefix="/coordinators", tags=["Coordinators"])


@router.post("", response_model=ApiResponse[CoordinatorResponse], status_code=201)
def create_coordinator(
    request: CreateCoordinatorRequest, service: CoordinatorService = Depends(),
    _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Coordinator created successfully", data=service.create_coordinator(request)
    )


@router.get("", response_model=ApiResponse[List[CoordinatorResponse]])
def get_all_coordinators(
    service: CoordinatorService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Coordinators retrieved successfully", data=service.get_all_coordinators()
    )


@router.get("/{coordinator_id}", response_model=ApiResponse[CoordinatorResponse])
def get_coordinator_by_id(
    coordinator_id: int, service: CoordinatorService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Coordinator retrieved successfully", data=service.get_coordinator_by_id(coordinator_id)
    )


@router.put("/{coordinator_id}", response_model=ApiResponse[CoordinatorResponse])
def update_coordinator(
    coordinator_id: int, request: UpdateCoordinatorRequest,
    service: CoordinatorService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Coordinator updated successfully",
        data=service.update_coordinator(coordinator_id, request),
    )
