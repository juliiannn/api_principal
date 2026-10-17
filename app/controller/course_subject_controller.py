from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_teacher, require_role
from app.dto.request.course_subject import CreateCourseSubjectRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.course_subject import CourseSubjectResponse
from app.model import Teacher, User
from app.service.course_subject_service import CourseSubjectService

router = APIRouter(prefix="/course-subjects", tags=["CourseSubjects"])


@router.post("", response_model=ApiResponse[CourseSubjectResponse], status_code=201)
def create_course_subject(
    request: CreateCourseSubjectRequest, service: CourseSubjectService = Depends(),
    _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Subject assigned to course successfully", data=service.create_course_subject(request)
    )


@router.get("", response_model=ApiResponse[List[CourseSubjectResponse]])
def get_all_course_subjects(
    service: CourseSubjectService = Depends(), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Course-subject assignments retrieved successfully",
        data=service.get_all_course_subjects(),
    )


@router.get("/me", response_model=ApiResponse[List[CourseSubjectResponse]])
def get_my_subjects(
    service: CourseSubjectService = Depends(), current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Your subjects retrieved successfully", data=service.get_my_subjects(current_teacher)
    )


@router.get("/{cs_id}", response_model=ApiResponse[CourseSubjectResponse])
def get_course_subject_by_id(
    cs_id: int, service: CourseSubjectService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    return ApiResponse(
        success=True, message="Course-subject assignment retrieved successfully",
        data=service.get_course_subject_by_id(cs_id),
    )


@router.get("/teacher/{teacher_id}", response_model=ApiResponse[List[CourseSubjectResponse]])
def get_course_subjects_by_teacher(
    teacher_id: int, service: CourseSubjectService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Teacher's subjects retrieved successfully",
        data=service.get_course_subjects_by_teacher(teacher_id, current_user),
    )


@router.put("/{cs_id}/deactivate", response_model=ApiResponse[CourseSubjectResponse])
def deactivate_course_subject(
    cs_id: int, service: CourseSubjectService = Depends(), _: User = Depends(require_role("ADMIN")),
):
    return ApiResponse(
        success=True, message="Assignment deactivated successfully", data=service.deactivate_course_subject(cs_id)
    )
