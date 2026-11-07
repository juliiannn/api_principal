from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import require_role
from app.dto.request.course import AssignDirectorTeacherRequest, CreateCourseRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.course import CourseResponse
from app.model import User
from app.service.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("", response_model=ApiResponse[CourseResponse], status_code=201)
def create_course(
    request: CreateCourseRequest, service: CourseService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(success=True, message="Course created successfully", data=service.create_course(request))


@router.put("/{course_id}", response_model=ApiResponse[CourseResponse])
def update_course(
    course_id: int, request: CreateCourseRequest,
    service: CourseService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Course updated successfully", data=service.update_course(course_id, request)
    )


@router.put("/{course_id}/director-teacher", response_model=ApiResponse[CourseResponse])
def assign_director_teacher(
    course_id: int, request: AssignDirectorTeacherRequest,
    service: CourseService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Director teacher assigned successfully",
        data=service.assign_director_teacher(course_id, request),
    )


@router.get("", response_model=ApiResponse[List[CourseResponse]])
def get_all_courses(
    include_inactive: bool = False, service: CourseService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Courses retrieved successfully",
        data=service.get_all_courses(include_inactive, current_user),
    )


@router.get("/{course_id}", response_model=ApiResponse[CourseResponse])
def get_course_by_id(
    course_id: int, service: CourseService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(success=True, message="Course retrieved successfully", data=service.get_course_by_id(course_id))


@router.put("/{course_id}/deactivate", response_model=ApiResponse[CourseResponse])
def deactivate_course(course_id: int, service: CourseService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(
        success=True, message="Course deactivated successfully", data=service.deactivate_course(course_id)
    )


@router.put("/{course_id}/activate", response_model=ApiResponse[CourseResponse])
def activate_course(course_id: int, service: CourseService = Depends(), _: User = Depends(require_role("ADMIN"))):
    return ApiResponse(success=True, message="Course activated successfully", data=service.activate_course(course_id))
