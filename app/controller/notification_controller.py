from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config.access import Access
from app.config.jwt_authentication import require_permission
from app.dto.request.notification import NotificationSettingUpdateRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.notification import (
    EmailConfigResponse, NotificationResponse, NotificationSettingResponse, NotificationStatsResponse,
)
from app.service.notification_admin_service import NotificationAdminService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

MODULE = "Notificaciones"


@router.get("", response_model=ApiResponse[List[NotificationResponse]])
def list_notifications(
    estado: Optional[str] = Query(None), evento: Optional[str] = Query(None), q: Optional[str] = Query(None),
    limit: int = Query(300, ge=1, le=2000),
    service: NotificationAdminService = Depends(), _: Access = Depends(require_permission(MODULE, "ver")),
):
    return ApiResponse(success=True, message="Notifications retrieved successfully",
                       data=service.list(estado, evento, q, limit))


@router.get("/stats", response_model=ApiResponse[NotificationStatsResponse])
def stats(service: NotificationAdminService = Depends(), _: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Statistics retrieved successfully", data=service.stats())


@router.get("/config", response_model=ApiResponse[EmailConfigResponse])
def config(service: NotificationAdminService = Depends(), _: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Email configuration retrieved", data=service.config())


@router.get("/settings", response_model=ApiResponse[List[NotificationSettingResponse]])
def settings_list(service: NotificationAdminService = Depends(), _: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Settings retrieved successfully", data=service.settings())


@router.put("/settings/{evento}", response_model=ApiResponse[NotificationSettingResponse])
def update_setting(
    evento: str, request: NotificationSettingUpdateRequest, service: NotificationAdminService = Depends(),
    _: Access = Depends(require_permission(MODULE, "editar")),
):
    return ApiResponse(success=True, message="Setting updated successfully", data=service.update_setting(evento, request.activo))


@router.post("/test", response_model=ApiResponse[NotificationResponse])
def send_test(service: NotificationAdminService = Depends(), access: Access = Depends(require_permission(MODULE, "crear"))):
    return ApiResponse(success=True, message="Test email processed", data=service.send_test(access.user))


@router.post("/{notification_id}/retry", response_model=ApiResponse[NotificationResponse])
def retry(notification_id: int, service: NotificationAdminService = Depends(),
          _: Access = Depends(require_permission(MODULE, "editar"))):
    return ApiResponse(success=True, message="Retry processed", data=service.retry(notification_id))
