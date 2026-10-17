from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_teacher, require_role
from app.dto.request.teacher import CreateTeacherRequest, UpdateTeacherRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.teacher import TeacherResponse
from app.model import Teacher, User
from app.service.teacher_service import TeacherService

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("", response_model=ApiResponse[TeacherResponse], status_code=201)
def create_teacher(
    request: CreateTeacherRequest, service: TeacherService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(success=True, message="Teacher created successfully", data=service.create_teacher(request))


@router.get("", response_model=ApiResponse[List[TeacherResponse]])
def get_all_teachers(
    service: TeacherService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(success=True, message="Teachers retrieved successfully", data=service.get_all_teachers())


@router.get("/me", response_model=ApiResponse[TeacherResponse])
def get_my_profile(current_teacher: Teacher = Depends(get_current_teacher), service: TeacherService = Depends()):
    return ApiResponse(success=True, message="Profile retrieved successfully", data=service.to_response(current_teacher))


@router.get("/{teacher_id}", response_model=ApiResponse[TeacherResponse])
def get_teacher_by_id(
    teacher_id: int, service: TeacherService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(success=True, message="Teacher retrieved successfully", data=service.get_teacher_by_id(teacher_id))


@router.put("/{teacher_id}", response_model=ApiResponse[TeacherResponse])
def update_teacher(
    teacher_id: int, request: UpdateTeacherRequest,
    service: TeacherService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Teacher updated successfully", data=service.update_teacher(teacher_id, request)
    )
