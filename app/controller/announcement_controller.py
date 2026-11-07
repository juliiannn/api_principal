from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.request.announcement import CreateAnnouncementRequest
from app.dto.response.announcement import AnnouncementResponse
from app.dto.response.api_response import ApiResponse
from app.model import User
from app.service.announcement_service import AnnouncementService

router = APIRouter(prefix="/announcements", tags=["Announcements"])

ALL_ROLES = ("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")


@router.post("", response_model=ApiResponse[AnnouncementResponse], status_code=201)
def create_announcement(
    request: CreateAnnouncementRequest, service: AnnouncementService = Depends(),
    current_user: User = Depends(require_role("RECTOR", "ADMIN")),
):
    return ApiResponse(
        success=True, message="Announcement published successfully",
        data=service.create_announcement(request, current_user),
    )


@router.get("", response_model=ApiResponse[List[AnnouncementResponse]])
def get_all_announcements(service: AnnouncementService = Depends(), _: User = Depends(require_role(*ALL_ROLES))):
    return ApiResponse(
        success=True, message="Announcements retrieved successfully", data=service.get_all_announcements()
    )


@router.get("/{announcement_id}", response_model=ApiResponse[AnnouncementResponse])
def get_announcement_by_id(
    announcement_id: int, service: AnnouncementService = Depends(), _: User = Depends(require_role(*ALL_ROLES)),
):
    return ApiResponse(
        success=True, message="Announcement retrieved successfully",
        data=service.get_announcement_by_id(announcement_id),
    )


@router.put("/{announcement_id}", response_model=ApiResponse[AnnouncementResponse])
def update_announcement(
    announcement_id: int, request: CreateAnnouncementRequest, service: AnnouncementService = Depends(),
    _: User = Depends(require_role("RECTOR", "ADMIN")),
):
    return ApiResponse(
        success=True, message="Announcement updated successfully",
        data=service.update_announcement(announcement_id, request),
    )


@router.put("/{announcement_id}/deactivate", response_model=ApiResponse[AnnouncementResponse])
def deactivate_announcement(
    announcement_id: int, service: AnnouncementService = Depends(),
    _: User = Depends(require_role("RECTOR", "ADMIN")),
):
    return ApiResponse(
        success=True, message="Announcement deactivated successfully",
        data=service.deactivate_announcement(announcement_id),
    )
