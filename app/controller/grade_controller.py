from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_teacher, require_role
from app.dto.request.grade import CreateGradeRequest, UpdateGradeRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.grade import GradeResponse
from app.model import Teacher, User
from app.service.grade_service import GradeService

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.post("", response_model=ApiResponse[GradeResponse], status_code=201)
def create_grade(
    request: CreateGradeRequest, service: GradeService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Grade registered successfully", data=service.create_grade(request, current_teacher)
    )


@router.put("/{grade_id}", response_model=ApiResponse[GradeResponse])
def update_grade(
    grade_id: int, request: UpdateGradeRequest, service: GradeService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Grade updated successfully", data=service.update_grade(grade_id, request, current_teacher)
    )


@router.get("/me", response_model=ApiResponse[List[GradeResponse]])
def get_my_grades(service: GradeService = Depends(), current_user: User = Depends(require_role("STUDENT"))):
    return ApiResponse(success=True, message="Grades retrieved successfully", data=service.get_my_grades(current_user))


@router.get("/{grade_id}", response_model=ApiResponse[GradeResponse])
def get_grade_by_id(
    grade_id: int, service: GradeService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")),
):
    return ApiResponse(
        success=True, message="Grade retrieved successfully", data=service.get_grade_by_id(grade_id, current_user)
    )


@router.get("/student/{student_id}", response_model=ApiResponse[List[GradeResponse]])
def get_grades_by_student(
    student_id: int, service: GradeService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")),
):
    return ApiResponse(
        success=True, message="Grades retrieved successfully",
        data=service.get_grades_by_student(student_id, current_user),
    )


@router.get("/course-subject/{cs_id}", response_model=ApiResponse[List[GradeResponse]])
def get_grades_by_course_subject(
    cs_id: int, service: GradeService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Grades retrieved successfully",
        data=service.get_grades_by_course_subject(cs_id, current_user),
    )
