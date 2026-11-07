from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_student, get_current_teacher, require_role
from app.dto.request.assignment import CreateAssignmentRequest, UpdateAssignmentRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.assignment import AssignmentResponse
from app.model import Student, Teacher, User
from app.service.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("", response_model=ApiResponse[AssignmentResponse], status_code=201)
def create_assignment(
    request: CreateAssignmentRequest, service: AssignmentService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Assignment published successfully",
        data=service.create_assignment(request, current_teacher),
    )


@router.get("/me", response_model=ApiResponse[List[AssignmentResponse]])
def get_my_assignments(
    service: AssignmentService = Depends(), current_student: Student = Depends(get_current_student),
):
    return ApiResponse(
        success=True, message="Assignments retrieved successfully", data=service.get_my_assignments(current_student)
    )


@router.get("/course-subject/{cs_id}", response_model=ApiResponse[List[AssignmentResponse]])
def get_assignments_by_course_subject(
    cs_id: int, service: AssignmentService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Assignments retrieved successfully",
        data=service.get_assignments_by_course_subject(cs_id, current_user),
    )


@router.get("/teacher/me", response_model=ApiResponse[List[AssignmentResponse]])
def get_my_teaching_assignments(
    service: AssignmentService = Depends(), current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Assignments retrieved successfully",
        data=service.get_my_teaching_assignments(current_teacher),
    )


@router.put("/{assignment_id}", response_model=ApiResponse[AssignmentResponse])
def update_assignment(
    assignment_id: int, request: UpdateAssignmentRequest, service: AssignmentService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Assignment updated successfully",
        data=service.update_assignment(assignment_id, request, current_teacher),
    )


@router.put("/{assignment_id}/deactivate", response_model=ApiResponse[AssignmentResponse])
def deactivate_assignment(
    assignment_id: int, service: AssignmentService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Assignment deactivated successfully",
        data=service.deactivate_assignment(assignment_id, current_teacher),
    )


@router.get("", response_model=ApiResponse[List[AssignmentResponse]])
def get_all_assignments(service: AssignmentService = Depends(), current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER"))):
    """Listado general (docente: solo sus materias)."""
    return ApiResponse(
        success=True, message="Assignments retrieved successfully", data=service.get_all_assignments(current_user)
    )
