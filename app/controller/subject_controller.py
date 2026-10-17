from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.request.subject import CreateSubjectRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.subject import SubjectResponse
from app.model import User
from app.service.subject_service import SubjectService

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("", response_model=ApiResponse[SubjectResponse], status_code=201)
def create_subject(
    request: CreateSubjectRequest, service: SubjectService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(success=True, message="Subject created successfully", data=service.create_subject(request))


@router.put("/{subject_id}", response_model=ApiResponse[SubjectResponse])
def update_subject(
    subject_id: int, request: CreateSubjectRequest,
    service: SubjectService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Subject updated successfully", data=service.update_subject(subject_id, request)
    )


@router.get("", response_model=ApiResponse[List[SubjectResponse]])
def get_all_subjects(
    include_inactive: bool = False, service: SubjectService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Subjects retrieved successfully",
        data=service.get_all_subjects(include_inactive, current_user),
    )


@router.get("/{subject_id}", response_model=ApiResponse[SubjectResponse])
def get_subject_by_id(
    subject_id: int, service: SubjectService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Subject retrieved successfully", data=service.get_subject_by_id(subject_id)
    )


@router.put("/{subject_id}/deactivate", response_model=ApiResponse[SubjectResponse])
def deactivate_subject(subject_id: int, service: SubjectService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(
        success=True, message="Subject deactivated successfully", data=service.deactivate_subject(subject_id)
    )


@router.put("/{subject_id}/activate", response_model=ApiResponse[SubjectResponse])
def activate_subject(subject_id: int, service: SubjectService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(
        success=True, message="Subject activated successfully", data=service.activate_subject(subject_id)
    )
