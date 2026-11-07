from datetime import datetime
from typing import List

from fastapi import Depends

from app.dto.request.submission import CreateSubmissionRequest, GradeSubmissionRequest, UpdateSubmissionRequest
from app.dto.response.submission import SubmissionResponse
from app.exception import (
    DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException,
)
from app.model import Student, Submission, Teacher, User
from app.repository.assignment_repository import AssignmentRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.submission_repository import SubmissionRepository
from app.service.current_user_service import CurrentUserService


class SubmissionService:
    """Entregas de tareas: el estudiante entrega, el docente califica y comenta, y ambos lo ven."""

    def __init__(
        self,
        submission_repository: SubmissionRepository = Depends(),
        assignment_repository: AssignmentRepository = Depends(),
        enrollment_repository: EnrollmentRepository = Depends(),
        current_user_service: CurrentUserService = Depends(),
    ):
        self.submission_repository = submission_repository
        self.assignment_repository = assignment_repository
        self.enrollment_repository = enrollment_repository
        self.current_user_service = current_user_service

    @staticmethod
    def to_response(s: Submission) -> SubmissionResponse:
        a = s.assignment
        cs = a.course_subject
        return SubmissionResponse(
            id=s.id, assignment_id=a.id, assignment_title=a.title, course_name=cs.course.name,
            subject_name=cs.subject.name, due_date=a.due_date, student_id=s.student_id,
            student_name=s.student.user.full_name, contenido=s.contenido, fecha_entrega=s.creado,
            actualizado=s.actualizado,
            entrega_tardia=bool(s.creado is not None and s.creado.date() > a.due_date),
            calificada=s.nota is not None, nota=s.nota, retroalimentacion=s.retroalimentacion,
            calificado_por_nombre=s.grader.user.full_name if s.grader else None,
            fecha_calificacion=s.fecha_calificacion, estado=s.estado,
        )

    def find_or_404(self, submission_id: int) -> Submission:
        s = self.submission_repository.find_active_by_id(submission_id)
        if s is None:
            raise ResourceNotFoundException(f"Submission with id {submission_id} not found")
        return s

    @staticmethod
    def _assert_own_and_ungraded(submission: Submission, student: Student) -> None:
        if submission.student_id != student.id:
            raise ForbiddenOperationException("You can only modify your own submissions")
        if submission.nota is not None:
            raise InvalidRequestException("A graded submission can no longer be modified")

    # ===== Estudiante =====

    def create_submission(self, request: CreateSubmissionRequest, current_student: Student) -> SubmissionResponse:
        assignment = self.assignment_repository.find_active_by_id(request.assignment_id)
        if assignment is None:
            raise ResourceNotFoundException(f"Assignment with id {request.assignment_id} not found")

        cs = assignment.course_subject
        if not cs.estado:
            raise InvalidRequestException("Cannot submit to an assignment of an inactive course-subject")
        if not self.enrollment_repository.exists_active_in_course(current_student.id, cs.course_id):
            raise ForbiddenOperationException("You can only submit assignments from your own course")
        if self.submission_repository.exists_active_by_assignment_and_student(assignment.id, current_student.id):
            raise DuplicateResourceException("You have already submitted this assignment; edit your submission instead")

        submission = Submission(
            assignment_id=assignment.id, student_id=current_student.id, contenido=request.contenido.strip()
        )
        return self.to_response(self.submission_repository.save(submission))

    def get_my_submissions(self, current_student: Student) -> List[SubmissionResponse]:
        items = self.submission_repository.find_active_by_student(current_student.id)
        return [self.to_response(s) for s in items]

    def update_submission(
        self, submission_id: int, request: UpdateSubmissionRequest, current_student: Student
    ) -> SubmissionResponse:
        submission = self.find_or_404(submission_id)
        self._assert_own_and_ungraded(submission, current_student)
        submission.contenido = request.contenido.strip()
        self.submission_repository.commit()
        self.submission_repository.refresh(submission)
        return self.to_response(submission)

    def deactivate_submission(self, submission_id: int, current_student: Student) -> SubmissionResponse:
        submission = self.find_or_404(submission_id)
        self._assert_own_and_ungraded(submission, current_student)
        submission.estado = False
        self.submission_repository.commit()
        self.submission_repository.refresh(submission)
        return self.to_response(submission)

    # ===== Docente =====

    def get_teacher_submissions(self, current_teacher: Teacher, only_pending: bool) -> List[SubmissionResponse]:
        items = self.submission_repository.find_active_by_teacher(current_teacher.id, only_pending)
        return [self.to_response(s) for s in items]

    def grade_submission(
        self, submission_id: int, request: GradeSubmissionRequest, current_teacher: Teacher
    ) -> SubmissionResponse:
        submission = self.find_or_404(submission_id)
        if submission.assignment.course_subject.teacher_id != current_teacher.id:
            raise ForbiddenOperationException("You can only grade submissions for subjects assigned to you")

        submission.nota = request.nota
        submission.retroalimentacion = request.retroalimentacion.strip()
        submission.calificado_por = current_teacher.id
        submission.fecha_calificacion = datetime.utcnow()
        self.submission_repository.commit()
        self.submission_repository.refresh(submission)
        return self.to_response(submission)

    # ===== Consulta (varios roles) =====

    def get_submissions_by_assignment(self, assignment_id: int, current_user: User) -> List[SubmissionResponse]:
        assignment = self.assignment_repository.find_active_by_id(assignment_id)
        if assignment is None:
            raise ResourceNotFoundException(f"Assignment with id {assignment_id} not found")
        if current_user.role.value == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_course_subject(current_user, assignment.course_subject_id)
        items = self.submission_repository.find_active_by_assignment(assignment_id)
        return [self.to_response(s) for s in items]

    def get_submission_by_id(self, submission_id: int, current_user: User) -> SubmissionResponse:
        submission = self.find_or_404(submission_id)
        role = current_user.role.value
        if role == "STUDENT":
            student = self.current_user_service.find_student(current_user)
            if student is None or student.id != submission.student_id:
                raise ForbiddenOperationException("You can only view your own submissions")
        elif role == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_course_subject(
                current_user, submission.assignment.course_subject_id
            )
        return self.to_response(submission)

    def _teacher_scope(self, current_user: User):
        """None = ve todo (personal directivo); Teacher = solo lo de sus materias."""
        if current_user.role_ref.nombre != "TEACHER":
            return None
        teacher = self.current_user_service.find_teacher(current_user)
        if teacher is None:
            raise ForbiddenOperationException("No teacher profile found for the authenticated user")
        return teacher

    def get_all_submissions(self, current_user: User) -> List[SubmissionResponse]:
        """Listado general: directivos ven todas las entregas; el docente, las de sus tareas."""
        teacher = self._teacher_scope(current_user)
        items = self.submission_repository.find_all_active() if teacher is None \
            else self.submission_repository.find_active_by_teacher(teacher.id)
        return [self.to_response(s) for s in items]
