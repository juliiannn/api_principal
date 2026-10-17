from datetime import date
from typing import List, Optional

from fastapi import Depends

from app.config.access import Access
from app.dto.request.piar import (
    CreatePiarAdjustmentRequest, CreatePiarGoalRequest, CreatePiarProgressRequest, CreatePiarRequest,
    PiarNeedInput, UpdatePiarProgressRequest, UpdatePiarRequest,
)
from app.dto.response.piar import (
    PiarAdjustmentResponse, PiarGoalResponse, PiarProgressResponse, PiarResponse,
)
from app.exception import (
    DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException,
)
from app.model import (
    PermissionScope, Piar, PiarAdjustment, PiarGoal, PiarNeed, PiarProgress, Student, Teacher,
)
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.piar_adjustment_repository import PiarAdjustmentRepository
from app.repository.piar_goal_repository import PiarGoalRepository
from app.repository.piar_need_repository import PiarNeedRepository
from app.repository.piar_progress_repository import PiarProgressRepository
from app.repository.piar_repository import PiarRepository
from app.repository.special_need_repository import SpecialNeedRepository
from app.repository.student_repository import StudentRepository
from app.repository.teacher_repository import TeacherRepository


class PiarService:
    """Plan Individual de Ajustes Razonables (Decreto 1421 de 2017)."""

    def __init__(
        self,
        piar_repository: PiarRepository = Depends(),
        piar_need_repository: PiarNeedRepository = Depends(),
        piar_goal_repository: PiarGoalRepository = Depends(),
        piar_adjustment_repository: PiarAdjustmentRepository = Depends(),
        piar_progress_repository: PiarProgressRepository = Depends(),
        special_need_repository: SpecialNeedRepository = Depends(),
        student_repository: StudentRepository = Depends(),
        teacher_repository: TeacherRepository = Depends(),
        course_subject_repository: CourseSubjectRepository = Depends(),
    ):
        self.piar_repository = piar_repository
        self.piar_need_repository = piar_need_repository
        self.piar_goal_repository = piar_goal_repository
        self.piar_adjustment_repository = piar_adjustment_repository
        self.piar_progress_repository = piar_progress_repository
        self.special_need_repository = special_need_repository
        self.student_repository = student_repository
        self.teacher_repository = teacher_repository
        self.course_subject_repository = course_subject_repository

    # ===== Respuestas =====

    @staticmethod
    def goal_to_response(g: PiarGoal) -> PiarGoalResponse:
        return PiarGoalResponse(
            id=g.id, piar_id=g.piar_id, course_subject_id=g.course_subject_id,
            subject_name=g.course_subject.subject.name if g.course_subject else None, descripcion=g.descripcion,
        )

    @staticmethod
    def adjustment_to_response(a: PiarAdjustment) -> PiarAdjustmentResponse:
        return PiarAdjustmentResponse(
            id=a.id, piar_id=a.piar_id, course_subject_id=a.course_subject_id,
            subject_name=a.course_subject.subject.name if a.course_subject else None,
            tipo=a.tipo, descripcion=a.descripcion,
        )

    @staticmethod
    def progress_to_response(p: PiarProgress) -> PiarProgressResponse:
        return PiarProgressResponse(
            id=p.id, piar_goal_id=p.piar_goal_id, period=p.period, nivel=p.nivel, observaciones=p.observaciones,
            registrado_por=p.registrado_por, teacher_name=p.teacher.user.full_name,
        )

    @classmethod
    def to_response(cls, p: Piar) -> PiarResponse:
        return PiarResponse(
            id=p.id, student_id=p.student_id, student_name=p.student.user.full_name, school_year=p.school_year,
            fecha_inicio=p.fecha_inicio, fecha_fin=p.fecha_fin, observaciones=p.observaciones,
            consentimiento_acudiente=p.consentimiento_acudiente,
            needs=[
                {"special_need_id": n.special_need_id, "nombre": n.special_need.nombre, "diagnostico": n.diagnostico}
                for n in p.needs if n.estado
            ],
            goals=[cls.goal_to_response(g) for g in p.goals if g.estado],
            adjustments=[cls.adjustment_to_response(a) for a in p.adjustments if a.estado],
            estado=p.estado,
        )

    # ===== Helpers de acceso =====

    def _find_piar_or_404(self, piar_id: int) -> Piar:
        piar = self.piar_repository.find_active_by_id(piar_id)
        if piar is None:
            raise ResourceNotFoundException(f"PIAR with id {piar_id} not found")
        return piar

    @staticmethod
    def _require_consent_for_teachers(access: Access, piar: Piar) -> None:
        """Los docentes (alcance ASSIGNED) solo acceden al PIAR cuando el acudiente ya lo autorizó."""
        if access.scope == PermissionScope.ASSIGNED and not piar.consentimiento_acudiente:
            raise ForbiddenOperationException("El acudiente aún no ha autorizado el PIAR de este estudiante")

    @staticmethod
    def _deny_teachers(access: Access) -> None:
        """Crear el plan o cambiar su consentimiento es labor de coordinación, no del docente."""
        if access.scope == PermissionScope.ASSIGNED:
            raise ForbiddenOperationException("Solo coordinación puede crear el PIAR o modificar los datos del plan")

    def _find_own_student(self, access: Access) -> Student:
        student = self.student_repository.find_active_by_user_id(access.user.id)
        if student is None:
            raise ResourceNotFoundException("No student profile found for the authenticated user")
        return student

    def _check_student_access(self, access: Access, student_id: int) -> None:
        """Aplica el alcance del permiso: ALL = cualquiera, OWN = solo el propio estudiante,
        ASSIGNED = solo estudiantes matriculados en cursos donde el docente dicta clase."""
        if access.scope == PermissionScope.ALL:
            return

        if access.scope == PermissionScope.OWN:
            if self._find_own_student(access).id != student_id:
                raise ForbiddenOperationException("You can only access your own PIAR")
            return

        teacher: Optional[Teacher] = self.teacher_repository.find_active_by_user_id(access.user.id)
        teaches_student = teacher is not None and self.course_subject_repository.teacher_teaches_student(
            teacher.id, student_id
        )
        if not teaches_student:
            raise ForbiddenOperationException("You can only access the PIAR of students from your assigned courses")

    def _validate_course_subject(self, cs_id: Optional[int]) -> None:
        if cs_id is None:
            return
        if self.course_subject_repository.find_active_by_id(cs_id) is None:
            raise ResourceNotFoundException(f"CourseSubject with id {cs_id} not found")

    def _attach_need(self, piar: Piar, item: PiarNeedInput) -> PiarNeed:
        need = self.special_need_repository.find_by_id(item.special_need_id)
        if need is None:
            raise ResourceNotFoundException(f"Special need with id {item.special_need_id} not found")

        existing = self.piar_need_repository.find_by_piar_and_need(piar.id, need.id)
        if existing is not None and existing.estado:
            raise DuplicateResourceException("This need is already registered in the PIAR")
        if existing is not None:  # estaba desactivada: se reactiva
            existing.estado = True
            existing.diagnostico = item.diagnostico
            return existing

        pn = PiarNeed(piar_id=piar.id, special_need_id=need.id, diagnostico=item.diagnostico)
        self.piar_need_repository.add(pn)
        return pn

    # ===== Plan =====

    def create_piar(self, request: CreatePiarRequest, access: Access) -> PiarResponse:
        student = self.student_repository.find_active_by_id(request.student_id)
        if student is None:
            raise ResourceNotFoundException(f"Student with id {request.student_id} not found")
        self._deny_teachers(access)
        self._check_student_access(access, student.id)

        if self.piar_repository.exists_by_student_and_school_year(student.id, request.school_year):
            raise DuplicateResourceException("The student already has a PIAR for that school year")

        start = request.fecha_inicio or date.today()
        if request.fecha_fin is not None and request.fecha_fin < start:
            raise InvalidRequestException("End date must not be before start date")

        piar = Piar(
            student_id=student.id, school_year=request.school_year, fecha_inicio=start, fecha_fin=request.fecha_fin,
            observaciones=request.observaciones, consentimiento_acudiente=request.consentimiento_acudiente,
            elaborado_por=access.user.id,
        )
        self.piar_repository.add(piar)
        self.piar_repository.flush()
        for item in request.needs:
            self._attach_need(piar, item)
            self.piar_repository.flush()
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        return self.to_response(piar)

    def get_my_piars(self, access: Access) -> List[PiarResponse]:
        student = self._find_own_student(access)
        piars = self.piar_repository.find_active_by_student_newest_first(student.id)
        return [self.to_response(p) for p in piars]

    def get_piars_by_student(self, student_id: int, access: Access) -> List[PiarResponse]:
        self._check_student_access(access, student_id)
        piars = self.piar_repository.find_active_by_student_newest_first(student_id)
        if access.scope == PermissionScope.ASSIGNED:
            piars = [p for p in piars if p.consentimiento_acudiente]
        return [self.to_response(p) for p in piars]

    def get_piar_by_id(self, piar_id: int, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        self._require_consent_for_teachers(access, piar)
        return self.to_response(piar)

    def update_piar(self, piar_id: int, request: UpdatePiarRequest, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        self._require_consent_for_teachers(access, piar)
        self._deny_teachers(access)
        if request.fecha_fin is not None and request.fecha_fin < piar.fecha_inicio:
            raise InvalidRequestException("End date must not be before start date")
        piar.fecha_fin = request.fecha_fin
        piar.observaciones = request.observaciones
        piar.consentimiento_acudiente = request.consentimiento_acudiente
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        return self.to_response(piar)

    # ===== Metas, ajustes y avance =====

    def create_goal(self, request: CreatePiarGoalRequest, access: Access) -> PiarGoalResponse:
        piar = self._find_piar_or_404(request.piar_id)
        self._check_student_access(access, piar.student_id)
        self._require_consent_for_teachers(access, piar)
        self._validate_course_subject(request.course_subject_id)
        goal = PiarGoal(
            piar_id=piar.id, course_subject_id=request.course_subject_id, descripcion=request.descripcion.strip()
        )
        return self.goal_to_response(self.piar_goal_repository.save(goal))

    def create_adjustment(self, request: CreatePiarAdjustmentRequest, access: Access) -> PiarAdjustmentResponse:
        piar = self._find_piar_or_404(request.piar_id)
        self._check_student_access(access, piar.student_id)
        self._require_consent_for_teachers(access, piar)
        self._validate_course_subject(request.course_subject_id)
        adjustment = PiarAdjustment(
            piar_id=piar.id, course_subject_id=request.course_subject_id, tipo=request.tipo,
            descripcion=request.descripcion.strip(),
        )
        return self.adjustment_to_response(self.piar_adjustment_repository.save(adjustment))

    def register_progress(
        self, request: CreatePiarProgressRequest, access: Access, teacher: Teacher
    ) -> PiarProgressResponse:
        goal = self.piar_goal_repository.find_active_by_id(request.piar_goal_id)
        if goal is None:
            raise ResourceNotFoundException(f"Goal with id {request.piar_goal_id} not found")
        self._check_student_access(access, goal.piar.student_id)
        self._require_consent_for_teachers(access, goal.piar)

        if self.piar_progress_repository.exists_by_goal_and_period(goal.id, request.period):
            raise DuplicateResourceException("Progress already registered for this goal and period")

        progress = PiarProgress(
            piar_goal_id=goal.id, period=request.period, nivel=request.nivel,
            observaciones=request.observaciones, registrado_por=teacher.id,
        )
        return self.progress_to_response(self.piar_progress_repository.save(progress))

    def update_progress(
        self, progress_id: int, request: UpdatePiarProgressRequest, access: Access
    ) -> PiarProgressResponse:
        progress = self.piar_progress_repository.find_active_by_id(progress_id)
        if progress is None:
            raise ResourceNotFoundException(f"Progress with id {progress_id} not found")
        self._check_student_access(access, progress.goal.piar.student_id)
        self._require_consent_for_teachers(access, progress.goal.piar)
        progress.nivel = request.nivel
        progress.observaciones = request.observaciones
        self.piar_progress_repository.commit()
        self.piar_progress_repository.refresh(progress)
        return self.progress_to_response(progress)

    def get_piar_progress(self, piar_id: int, access: Access) -> List[PiarProgressResponse]:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        self._require_consent_for_teachers(access, piar)
        items = self.piar_progress_repository.find_active_by_piar_ordered_by_period(piar.id)
        return [self.progress_to_response(p) for p in items]

    # ===== Necesidades del plan =====

    def add_need(self, piar_id: int, request: PiarNeedInput, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        self._require_consent_for_teachers(access, piar)
        self._attach_need(piar, request)
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        return self.to_response(piar)

    def remove_need(self, piar_id: int, special_need_id: int, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        self._require_consent_for_teachers(access, piar)
        pn = self.piar_need_repository.find_active_by_piar_and_need(piar.id, special_need_id)
        if pn is None:
            raise ResourceNotFoundException("That need is not registered in the PIAR")
        pn.estado = False
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        return self.to_response(piar)
