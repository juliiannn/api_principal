from typing import List

from fastapi import APIRouter, Depends

from app.config.jwt_authentication import get_current_student, get_current_teacher, require_role
from app.dto.request.submission import CreateSubmissionRequest, GradeSubmissionRequest, UpdateSubmissionRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.submission import SubmissionResponse
from app.model import Student, Teacher, User
from app.service.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Submissions"])


# ===== Estudiante =====

@router.post("", response_model=ApiResponse[SubmissionResponse], status_code=201)
def create_submission(
    request: CreateSubmissionRequest, service: SubmissionService = Depends(),
    _: User = Depends(require_role("STUDENT")), current_student: Student = Depends(get_current_student),
):
    return ApiResponse(
        success=True, message="Submission created successfully",
        data=service.create_submission(request, current_student),
    )


@router.get("/me", response_model=ApiResponse[List[SubmissionResponse]])
def get_my_submissions(
    service: SubmissionService = Depends(),
    _: User = Depends(require_role("STUDENT")), current_student: Student = Depends(get_current_student),
):
    return ApiResponse(
        success=True, message="Submissions retrieved successfully", data=service.get_my_submissions(current_student)
    )


# ===== Docente (rutas fijas antes de /{submission_id}) =====

@router.get("/teacher/me", response_model=ApiResponse[List[SubmissionResponse]])
def get_teacher_submissions(
    pending: bool = False, service: SubmissionService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Submissions retrieved successfully",
        data=service.get_teacher_submissions(current_teacher, pending),
    )


@router.get("/assignment/{assignment_id}", response_model=ApiResponse[List[SubmissionResponse]])
def get_submissions_by_assignment(
    assignment_id: int, service: SubmissionService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER")),
):
    return ApiResponse(
        success=True, message="Submissions retrieved successfully",
        data=service.get_submissions_by_assignment(assignment_id, current_user),
    )


# ===== Detalle y modificación =====

@router.get("/{submission_id}", response_model=ApiResponse[SubmissionResponse])
def get_submission_by_id(
    submission_id: int, service: SubmissionService = Depends(),
    current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER", "STUDENT")),
):
    return ApiResponse(
        success=True, message="Submission retrieved successfully",
        data=service.get_submission_by_id(submission_id, current_user),
    )


@router.put("/{submission_id}", response_model=ApiResponse[SubmissionResponse])
def update_submission(
    submission_id: int, request: UpdateSubmissionRequest, service: SubmissionService = Depends(),
    _: User = Depends(require_role("STUDENT")), current_student: Student = Depends(get_current_student),
):
    return ApiResponse(
        success=True, message="Submission updated successfully",
        data=service.update_submission(submission_id, request, current_student),
    )


@router.put("/{submission_id}/grade", response_model=ApiResponse[SubmissionResponse])
def grade_submission(
    submission_id: int, request: GradeSubmissionRequest, service: SubmissionService = Depends(),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    return ApiResponse(
        success=True, message="Submission graded successfully",
        data=service.grade_submission(submission_id, request, current_teacher),
    )


@router.put("/{submission_id}/deactivate", response_model=ApiResponse[SubmissionResponse])
def deactivate_submission(
    submission_id: int, service: SubmissionService = Depends(),
    _: User = Depends(require_role("STUDENT")), current_student: Student = Depends(get_current_student),
):
    return ApiResponse(
        success=True, message="Submission deactivated successfully",
        data=service.deactivate_submission(submission_id, current_student),
    )


@router.get("", response_model=ApiResponse[List[SubmissionResponse]])
def get_all_submissions(service: SubmissionService = Depends(), current_user: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR", "TEACHER"))):
    """Listado general (docente: solo las entregas de sus tareas)."""
    return ApiResponse(
        success=True, message="Submissions retrieved successfully", data=service.get_all_submissions(current_user)
    )
