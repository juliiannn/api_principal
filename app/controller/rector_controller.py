from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.request.rector import CreateRectorRequest, UpdateRectorRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.rector import RectorResponse
from app.model import User
from app.service.rector_service import RectorService

router = APIRouter(prefix="/rectors", tags=["Rectors"])


@router.post("", response_model=ApiResponse[RectorResponse], status_code=201)
def create_rector(
    request: CreateRectorRequest, service: RectorService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(success=True, message="Rector created successfully", data=service.create_rector(request))


@router.get("", response_model=ApiResponse[List[RectorResponse]])
def get_all_rectors(service: RectorService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="Rectors retrieved successfully", data=service.get_all_rectors())


@router.get("/{rector_id}", response_model=ApiResponse[RectorResponse])
def get_rector_by_id(rector_id: int, service: RectorService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="Rector retrieved successfully", data=service.get_rector_by_id(rector_id))


@router.put("/{rector_id}", response_model=ApiResponse[RectorResponse])
def update_rector(
    rector_id: int, request: UpdateRectorRequest,
    service: RectorService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Rector updated successfully", data=service.update_rector(rector_id, request)
    )
