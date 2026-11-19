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
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.piar_adjustment_repository import PiarAdjustmentRepository
from app.repository.piar_goal_repository import PiarGoalRepository
from app.repository.piar_need_repository import PiarNeedRepository
from app.repository.piar_progress_repository import PiarProgressRepository
from app.repository.piar_repository import PiarRepository
from app.repository.special_need_repository import SpecialNeedRepository
from app.repository.student_repository import StudentRepository
from app.repository.teacher_repository import TeacherRepository
from app.service.platform_notifier import PlatformNotifier


# El PIAR lo elaboran los docentes de aula con el docente de apoyo, la familia y el estudiante (Decreto 1421 de 2017).
# Por eso el docente (alcance ASSIGNED en role_modules) crea, edita y desactiva el PIAR, pero SOLO de los
# estudiantes de sus cursos; coordinación y administración (alcance ALL) lo hacen para cualquier estudiante.
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
        enrollment_repository: EnrollmentRepository = Depends(),
        notifier: PlatformNotifier = Depends(),
    ):
        self.notifier = notifier
        self.piar_repository = piar_repository
        self.piar_need_repository = piar_need_repository
        self.piar_goal_repository = piar_goal_repository
        self.piar_adjustment_repository = piar_adjustment_repository
        self.piar_progress_repository = piar_progress_repository
        self.special_need_repository = special_need_repository
        self.student_repository = student_repository
        self.teacher_repository = teacher_repository
        self.course_subject_repository = course_subject_repository
        self.enrollment_repository = enrollment_repository

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

    def to_response(self, p: Piar, courses: Optional[dict] = None) -> PiarResponse:
        # courses: {student_id: (course_id, course_name)} ya consultado para todo el listado (evita una consulta por PIAR)
        if courses is None:
            courses = self.enrollment_repository.find_current_courses([p.student_id])
        course_id, course_name = courses.get(p.student_id, (None, None))
        return PiarResponse(
            course_id=course_id,
            course_name=course_name,
            id=p.id, student_id=p.student_id, student_name=p.student.user.full_name, school_year=p.school_year,
            fecha_inicio=p.fecha_inicio, fecha_fin=p.fecha_fin, observaciones=p.observaciones,
            consentimiento_acudiente=p.consentimiento_acudiente,
            needs=[
                {"special_need_id": n.special_need_id, "nombre": n.special_need.nombre, "diagnostico": n.diagnostico}
                for n in p.needs if n.estado
            ],
            goals=[self.goal_to_response(g) for g in p.goals if g.estado],
            adjustments=[self.adjustment_to_response(a) for a in p.adjustments if a.estado],
            estado=p.estado, creado=p.creado, actualizado=p.actualizado,
        )

    def to_responses(self, piars: List[Piar]) -> List[PiarResponse]:
        courses = self.enrollment_repository.find_current_courses(list({p.student_id for p in piars}))
        return [self.to_response(p, courses) for p in piars]

    # ===== Helpers de acceso =====

    def _find_piar_or_404(self, piar_id: int) -> Piar:
        piar = self.piar_repository.find_active_by_id(piar_id)
        if piar is None:
            raise ResourceNotFoundException(f"PIAR with id {piar_id} not found")
        return piar

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

    def _validate_course_subject(self, cs_id: Optional[int], student_id: int, access: Access) -> None:
        """La materia (opcional) debe dictarse en el curso actual del estudiante; un docente solo
        puede usar materias que él mismo dicta. Sin materia, la meta o el ajuste aplica a todas."""
        if cs_id is None:
            return
        cs = self.course_subject_repository.find_active_by_id(cs_id)
        if cs is None:
            raise ResourceNotFoundException(f"CourseSubject with id {cs_id} not found")
        enrollment = self.enrollment_repository.find_current_by_student(student_id)
        if enrollment is None or enrollment.course_id != cs.course_id:
            raise InvalidRequestException("The subject does not belong to the student's current course")
        if access.scope == PermissionScope.ASSIGNED:
            teacher = self.teacher_repository.find_active_by_user_id(access.user.id)
            if teacher is None or cs.teacher_id != teacher.id:
                raise ForbiddenOperationException("You can only use subjects you teach")

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
        response = self.to_response(piar)
        self.notifier.piar_changed(student.id, f"Se creó el PIAR del año {piar.school_year}", access.user)
        return response

    def get_my_piars(self, access: Access) -> List[PiarResponse]:
        student = self._find_own_student(access)
        piars = self.piar_repository.find_active_by_student_newest_first(student.id)
        return self.to_responses(piars)

    def get_my_progress(self, access: Access) -> List[PiarProgressResponse]:
        student = self._find_own_student(access)
        piars = self.piar_repository.find_active_by_student_newest_first(student.id)
        if not piars:
            return []
        items = self.piar_progress_repository.find_active_by_piar_ordered_by_period(piars[0].id)
        return [self.progress_to_response(p) for p in items]

    def get_piars_by_student(self, student_id: int, access: Access) -> List[PiarResponse]:
        self._check_student_access(access, student_id)
        piars = self.piar_repository.find_active_by_student_newest_first(student_id)
        return self.to_responses(piars)

    def get_piar_by_id(self, piar_id: int, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        return self.to_response(piar)

    def update_piar(self, piar_id: int, request: UpdatePiarRequest, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        if request.fecha_fin is not None and request.fecha_fin < piar.fecha_inicio:
            raise InvalidRequestException("End date must not be before start date")
        piar.fecha_fin = request.fecha_fin
        piar.observaciones = request.observaciones
        piar.consentimiento_acudiente = request.consentimiento_acudiente
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        response = self.to_response(piar)
        self.notifier.piar_changed(piar.student_id, f"Se actualizaron los datos generales del PIAR {piar.school_year}", access.user)
        return response

    # ===== Metas, ajustes y avance =====

    def create_goal(self, request: CreatePiarGoalRequest, access: Access) -> PiarGoalResponse:
        piar = self._find_piar_or_404(request.piar_id)
        self._check_student_access(access, piar.student_id)
        self._validate_course_subject(request.course_subject_id, piar.student_id, access)
        goal = PiarGoal(
            piar_id=piar.id, course_subject_id=request.course_subject_id, descripcion=request.descripcion.strip()
        )
        response = self.goal_to_response(self.piar_goal_repository.save(goal))
        self.notifier.piar_changed(piar.student_id, f"Nueva meta{self._in_subject(response.subject_name)}", access.user)
        return response

    @staticmethod
    def _in_subject(name) -> str:
        return f" en {name}" if name else " general"

    def create_adjustment(self, request: CreatePiarAdjustmentRequest, access: Access) -> PiarAdjustmentResponse:
        piar = self._find_piar_or_404(request.piar_id)
        self._check_student_access(access, piar.student_id)
        self._validate_course_subject(request.course_subject_id, piar.student_id, access)
        adjustment = PiarAdjustment(
            piar_id=piar.id, course_subject_id=request.course_subject_id, tipo=request.tipo,
            descripcion=request.descripcion.strip(),
        )
        response = self.adjustment_to_response(self.piar_adjustment_repository.save(adjustment))
        self.notifier.piar_changed(piar.student_id, f"Nuevo ajuste razonable{self._in_subject(response.subject_name)}", access.user)
        return response

    def register_progress(
        self, request: CreatePiarProgressRequest, access: Access, teacher: Teacher
    ) -> PiarProgressResponse:
        goal = self.piar_goal_repository.find_active_by_id(request.piar_goal_id)
        if goal is None:
            raise ResourceNotFoundException(f"Goal with id {request.piar_goal_id} not found")
        self._check_student_access(access, goal.piar.student_id)

        if self.piar_progress_repository.exists_by_goal_and_period(goal.id, request.period):
            raise DuplicateResourceException("Progress already registered for this goal and period")

        progress = PiarProgress(
            piar_goal_id=goal.id, period=request.period, nivel=request.nivel,
            observaciones=request.observaciones, registrado_por=teacher.id,
        )
        response = self.progress_to_response(self.piar_progress_repository.save(progress))
        self.notifier.piar_changed(goal.piar.student_id, f"Se registró el avance del periodo {str(getattr(request.period, 'value', request.period)).replace('PERIOD_', '')}", access.user)
        return response

    def update_progress(
        self, progress_id: int, request: UpdatePiarProgressRequest, access: Access
    ) -> PiarProgressResponse:
        progress = self.piar_progress_repository.find_active_by_id(progress_id)
        if progress is None:
            raise ResourceNotFoundException(f"Progress with id {progress_id} not found")
        self._check_student_access(access, progress.goal.piar.student_id)
        progress.nivel = request.nivel
        progress.observaciones = request.observaciones
        self.piar_progress_repository.commit()
        self.piar_progress_repository.refresh(progress)
        response = self.progress_to_response(progress)
        self.notifier.piar_changed(progress.goal.piar.student_id, f"Se modificó el avance del periodo {str(getattr(progress.period, 'value', progress.period)).replace('PERIOD_', '')}", access.user)
        return response

    def get_piar_progress(self, piar_id: int, access: Access) -> List[PiarProgressResponse]:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        items = self.piar_progress_repository.find_active_by_piar_ordered_by_period(piar.id)
        return [self.progress_to_response(p) for p in items]

    def deactivate_goal(self, goal_id: int, access: Access) -> PiarGoalResponse:
        goal = self.piar_goal_repository.find_active_by_id(goal_id)
        if goal is None:
            raise ResourceNotFoundException(f"Goal with id {goal_id} not found")
        self._check_student_access(access, goal.piar.student_id)
        goal.estado = False
        self.piar_goal_repository.commit()
        self.piar_goal_repository.refresh(goal)
        return self.goal_to_response(goal)

    def deactivate_adjustment(self, adjustment_id: int, access: Access) -> PiarAdjustmentResponse:
        adjustment = self.piar_adjustment_repository.find_active_by_id(adjustment_id)
        if adjustment is None:
            raise ResourceNotFoundException(f"Adjustment with id {adjustment_id} not found")
        self._check_student_access(access, adjustment.piar.student_id)
        adjustment.estado = False
        self.piar_adjustment_repository.commit()
        self.piar_adjustment_repository.refresh(adjustment)
        return self.adjustment_to_response(adjustment)

    # ===== Necesidades del plan =====

    def add_need(self, piar_id: int, request: PiarNeedInput, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        self._attach_need(piar, request)
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        return self.to_response(piar)

    def remove_need(self, piar_id: int, special_need_id: int, access: Access) -> PiarResponse:
        piar = self._find_piar_or_404(piar_id)
        self._check_student_access(access, piar.student_id)
        pn = self.piar_need_repository.find_active_by_piar_and_need(piar.id, special_need_id)
        if pn is None:
            raise ResourceNotFoundException("That need is not registered in the PIAR")
        pn.estado = False
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        return self.to_response(piar)

    # ===== Listado general y borrado lógico =====

    def get_all_piars(self, access: Access) -> List[PiarResponse]:
        """ALL = todos; ASSIGNED = los estudiantes de los cursos del docente; OWN = el propio. Incluye inactivos (para reactivarlos)."""
        if access.scope == PermissionScope.OWN:
            return self.get_my_piars(access)
        piars = self.piar_repository.find_all_newest_first()
        if access.scope == PermissionScope.ASSIGNED:
            teacher = self.teacher_repository.find_active_by_user_id(access.user.id)
            mine = self.course_subject_repository.student_ids_taught_by(teacher.id) if teacher else set()
            piars = [p for p in piars if p.student_id in mine]
        return self.to_responses(piars)

    def set_piar_status(self, piar_id: int, active: bool, access: Access) -> PiarResponse:
        """Desactivar = borrado lógico (estado FALSE). Reactivar lo vuelve a dejar vigente."""
        piar = self.piar_repository.find_by_id(piar_id)
        if piar is None:
            raise ResourceNotFoundException(f"PIAR with id {piar_id} not found")
        self._check_student_access(access, piar.student_id)
        piar.estado = active
        self.piar_repository.commit()
        self.piar_repository.refresh(piar)
        return self.to_response(piar)
