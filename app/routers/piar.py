from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import Access, get_current_teacher, require_permission
from app.exceptions import (
    DuplicateResourceException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException,
)
from app.models import (
    CourseSubject, Enrollment, EnrollmentStatus, PermissionScope, Piar, PiarAdjustment, PiarGoal, PiarNeed,
    PiarProgress, SpecialNeed, Student, Teacher,
)
from app.schemas import (
    ApiResponse, CreatePiarAdjustmentRequest, CreatePiarGoalRequest, CreatePiarProgressRequest, CreatePiarRequest,
    PiarAdjustmentResponse, PiarGoalResponse, PiarNeedInput, PiarProgressResponse, PiarResponse,
    UpdatePiarProgressRequest, UpdatePiarRequest,
)

router = APIRouter(prefix="/piars", tags=["PIAR"])

MODULE = "PIAR"


# ===== Respuestas =====

def goal_to_response(g: PiarGoal) -> PiarGoalResponse:
    return PiarGoalResponse(
        id=g.id, piar_id=g.piar_id, course_subject_id=g.course_subject_id,
        subject_name=g.course_subject.subject.name if g.course_subject else None, descripcion=g.descripcion,
    )


def adjustment_to_response(a: PiarAdjustment) -> PiarAdjustmentResponse:
    return PiarAdjustmentResponse(
        id=a.id, piar_id=a.piar_id, course_subject_id=a.course_subject_id,
        subject_name=a.course_subject.subject.name if a.course_subject else None, tipo=a.tipo, descripcion=a.descripcion,
    )


def progress_to_response(p: PiarProgress) -> PiarProgressResponse:
    return PiarProgressResponse(
        id=p.id, piar_goal_id=p.piar_goal_id, period=p.period, nivel=p.nivel, observaciones=p.observaciones,
        registrado_por=p.registrado_por, teacher_name=p.teacher.user.full_name,
    )


def to_response(p: Piar) -> PiarResponse:
    return PiarResponse(
        id=p.id, student_id=p.student_id, student_name=p.student.user.full_name, school_year=p.school_year,
        fecha_inicio=p.fecha_inicio, fecha_fin=p.fecha_fin, observaciones=p.observaciones,
        consentimiento_acudiente=p.consentimiento_acudiente,
        needs=[
            {"special_need_id": n.special_need_id, "nombre": n.special_need.nombre, "diagnostico": n.diagnostico}
            for n in p.needs if n.estado
        ],
        goals=[goal_to_response(g) for g in p.goals if g.estado],
        adjustments=[adjustment_to_response(a) for a in p.adjustments if a.estado],
        estado=p.estado,
    )


# ===== Helpers de acceso =====

def find_piar_or_404(db: Session, piar_id: int) -> Piar:
    piar = db.query(Piar).filter(Piar.id == piar_id, Piar.estado.is_(True)).first()
    if piar is None:
        raise ResourceNotFoundException(f"PIAR with id {piar_id} not found")
    return piar


def require_consent_for_teachers(access: Access, piar: Piar):
    """Los docentes (alcance ASSIGNED) solo acceden al PIAR cuando el acudiente ya lo autorizó."""
    if access.scope == PermissionScope.ASSIGNED and not piar.consentimiento_acudiente:
        raise ForbiddenOperationException("El acudiente aún no ha autorizado el PIAR de este estudiante")


def deny_teachers(access: Access):
    """Crear el plan o cambiar su consentimiento es labor de coordinación, no del docente."""
    if access.scope == PermissionScope.ASSIGNED:
        raise ForbiddenOperationException("Solo coordinación puede crear el PIAR o modificar los datos del plan")


def find_own_student(db: Session, access: Access) -> Student:
    student = db.query(Student).filter(Student.user_id == access.user.id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException("No student profile found for the authenticated user")
    return student


def check_student_access(db: Session, access: Access, student_id: int):
    """Aplica el alcance del permiso: ALL = cualquiera, OWN = solo el propio estudiante,
    ASSIGNED = solo estudiantes matriculados en cursos donde el docente dicta clase."""
    if access.scope == PermissionScope.ALL:
        return

    if access.scope == PermissionScope.OWN:
        if find_own_student(db, access).id != student_id:
            raise ForbiddenOperationException("You can only access your own PIAR")
        return

    teacher = db.query(Teacher).filter(Teacher.user_id == access.user.id, Teacher.estado.is_(True)).first()
    teaches_student = None
    if teacher is not None:
        teaches_student = (
            db.query(CourseSubject.id)
            .join(Enrollment, Enrollment.course_id == CourseSubject.course_id)
            .filter(
                CourseSubject.teacher_id == teacher.id, CourseSubject.estado.is_(True),
                Enrollment.student_id == student_id, Enrollment.status == EnrollmentStatus.ACTIVE,
                Enrollment.estado.is_(True),
            )
            .first()
        )
    if teaches_student is None:
        raise ForbiddenOperationException("You can only access the PIAR of students from your assigned courses")


def validate_course_subject(db: Session, cs_id):
    if cs_id is None:
        return
    cs = db.query(CourseSubject).filter(CourseSubject.id == cs_id, CourseSubject.estado.is_(True)).first()
    if cs is None:
        raise ResourceNotFoundException(f"CourseSubject with id {cs_id} not found")


def attach_need(db: Session, piar: Piar, item: PiarNeedInput):
    need = db.query(SpecialNeed).filter(SpecialNeed.id == item.special_need_id, SpecialNeed.estado.is_(True)).first()
    if need is None:
        raise ResourceNotFoundException(f"Special need with id {item.special_need_id} not found")
    existing = db.query(PiarNeed).filter(PiarNeed.piar_id == piar.id, PiarNeed.special_need_id == need.id).first()
    if existing is not None and existing.estado:
        raise DuplicateResourceException("This need is already registered in the PIAR")
    if existing is not None:  # estaba desactivada: se reactiva
        existing.estado = True
        existing.diagnostico = item.diagnostico
        return existing
    pn = PiarNeed(piar_id=piar.id, special_need_id=need.id, diagnostico=item.diagnostico)
    db.add(pn)
    return pn


# ===== Plan =====

@router.post("", response_model=ApiResponse[PiarResponse], status_code=201)
def create_piar(request: CreatePiarRequest, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "crear"))):
    student = db.query(Student).filter(Student.id == request.student_id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException(f"Student with id {request.student_id} not found")
    deny_teachers(access)
    check_student_access(db, access, student.id)

    if db.query(Piar).filter(Piar.student_id == student.id, Piar.school_year == request.school_year).first():
        raise DuplicateResourceException("The student already has a PIAR for that school year")

    start = request.fecha_inicio or date.today()
    if request.fecha_fin is not None and request.fecha_fin < start:
        raise InvalidRequestException("End date must not be before start date")

    piar = Piar(
        student_id=student.id, school_year=request.school_year, fecha_inicio=start, fecha_fin=request.fecha_fin,
        observaciones=request.observaciones, consentimiento_acudiente=request.consentimiento_acudiente,
        elaborado_por=access.user.id,
    )
    db.add(piar)
    db.flush()
    for item in request.needs:
        attach_need(db, piar, item)
        db.flush()
    db.commit()
    db.refresh(piar)
    return ApiResponse(success=True, message="PIAR created successfully", data=to_response(piar))


@router.get("/me", response_model=ApiResponse[List[PiarResponse]])
def get_my_piars(db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "ver"))):
    student = find_own_student(db, access)
    piars = db.query(Piar).filter(Piar.student_id == student.id, Piar.estado.is_(True)).order_by(Piar.school_year.desc()).all()
    return ApiResponse(success=True, message="PIAR retrieved successfully", data=[to_response(p) for p in piars])


@router.get("/student/{student_id}", response_model=ApiResponse[List[PiarResponse]])
def get_piars_by_student(student_id: int, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "ver"))):
    check_student_access(db, access, student_id)
    piars = db.query(Piar).filter(Piar.student_id == student_id, Piar.estado.is_(True)).order_by(Piar.school_year.desc()).all()
    if access.scope == PermissionScope.ASSIGNED:
        piars = [p for p in piars if p.consentimiento_acudiente]
    return ApiResponse(success=True, message="PIAR retrieved successfully", data=[to_response(p) for p in piars])


# ===== Metas, ajustes y avance (rutas fijas antes de /{piar_id}) =====

@router.post("/goals", response_model=ApiResponse[PiarGoalResponse], status_code=201)
def create_goal(request: CreatePiarGoalRequest, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "crear"))):
    piar = find_piar_or_404(db, request.piar_id)
    check_student_access(db, access, piar.student_id)
    require_consent_for_teachers(access, piar)
    validate_course_subject(db, request.course_subject_id)
    goal = PiarGoal(piar_id=piar.id, course_subject_id=request.course_subject_id, descripcion=request.descripcion.strip())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return ApiResponse(success=True, message="Goal created successfully", data=goal_to_response(goal))


@router.post("/adjustments", response_model=ApiResponse[PiarAdjustmentResponse], status_code=201)
def create_adjustment(request: CreatePiarAdjustmentRequest, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "crear"))):
    piar = find_piar_or_404(db, request.piar_id)
    check_student_access(db, access, piar.student_id)
    require_consent_for_teachers(access, piar)
    validate_course_subject(db, request.course_subject_id)
    adjustment = PiarAdjustment(
        piar_id=piar.id, course_subject_id=request.course_subject_id, tipo=request.tipo, descripcion=request.descripcion.strip(),
    )
    db.add(adjustment)
    db.commit()
    db.refresh(adjustment)
    return ApiResponse(success=True, message="Adjustment created successfully", data=adjustment_to_response(adjustment))


@router.post("/progress", response_model=ApiResponse[PiarProgressResponse], status_code=201)
def register_progress(
    request: CreatePiarProgressRequest, db: Session = Depends(get_db),
    access: Access = Depends(require_permission(MODULE, "crear")), teacher: Teacher = Depends(get_current_teacher),
):
    goal = db.query(PiarGoal).filter(PiarGoal.id == request.piar_goal_id, PiarGoal.estado.is_(True)).first()
    if goal is None:
        raise ResourceNotFoundException(f"Goal with id {request.piar_goal_id} not found")
    check_student_access(db, access, goal.piar.student_id)
    require_consent_for_teachers(access, goal.piar)

    if db.query(PiarProgress).filter(PiarProgress.piar_goal_id == goal.id, PiarProgress.period == request.period).first():
        raise DuplicateResourceException("Progress already registered for this goal and period")

    progress = PiarProgress(
        piar_goal_id=goal.id, period=request.period, nivel=request.nivel,
        observaciones=request.observaciones, registrado_por=teacher.id,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return ApiResponse(success=True, message="Progress registered successfully", data=progress_to_response(progress))


@router.put("/progress/{progress_id}", response_model=ApiResponse[PiarProgressResponse])
def update_progress(progress_id: int, request: UpdatePiarProgressRequest, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "editar"))):
    progress = db.query(PiarProgress).filter(PiarProgress.id == progress_id, PiarProgress.estado.is_(True)).first()
    if progress is None:
        raise ResourceNotFoundException(f"Progress with id {progress_id} not found")
    check_student_access(db, access, progress.goal.piar.student_id)
    require_consent_for_teachers(access, progress.goal.piar)
    progress.nivel = request.nivel
    progress.observaciones = request.observaciones
    db.commit()
    db.refresh(progress)
    return ApiResponse(success=True, message="Progress updated successfully", data=progress_to_response(progress))


# ===== Detalle del plan =====

@router.get("/{piar_id}", response_model=ApiResponse[PiarResponse])
def get_piar_by_id(piar_id: int, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "ver"))):
    piar = find_piar_or_404(db, piar_id)
    check_student_access(db, access, piar.student_id)
    require_consent_for_teachers(access, piar)
    return ApiResponse(success=True, message="PIAR retrieved successfully", data=to_response(piar))


@router.put("/{piar_id}", response_model=ApiResponse[PiarResponse])
def update_piar(piar_id: int, request: UpdatePiarRequest, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "editar"))):
    piar = find_piar_or_404(db, piar_id)
    check_student_access(db, access, piar.student_id)
    require_consent_for_teachers(access, piar)
    deny_teachers(access)
    if request.fecha_fin is not None and request.fecha_fin < piar.fecha_inicio:
        raise InvalidRequestException("End date must not be before start date")
    piar.fecha_fin = request.fecha_fin
    piar.observaciones = request.observaciones
    piar.consentimiento_acudiente = request.consentimiento_acudiente
    db.commit()
    db.refresh(piar)
    return ApiResponse(success=True, message="PIAR updated successfully", data=to_response(piar))


@router.get("/{piar_id}/progress", response_model=ApiResponse[List[PiarProgressResponse]])
def get_piar_progress(piar_id: int, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "ver"))):
    piar = find_piar_or_404(db, piar_id)
    check_student_access(db, access, piar.student_id)
    require_consent_for_teachers(access, piar)
    items = (
        db.query(PiarProgress).join(PiarGoal, PiarProgress.piar_goal_id == PiarGoal.id)
        .filter(PiarGoal.piar_id == piar.id, PiarGoal.estado.is_(True), PiarProgress.estado.is_(True))
        .order_by(PiarProgress.period).all()
    )
    return ApiResponse(success=True, message="Progress retrieved successfully", data=[progress_to_response(p) for p in items])


@router.post("/{piar_id}/needs", response_model=ApiResponse[PiarResponse], status_code=201)
def add_need(piar_id: int, request: PiarNeedInput, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "crear"))):
    piar = find_piar_or_404(db, piar_id)
    check_student_access(db, access, piar.student_id)
    require_consent_for_teachers(access, piar)
    attach_need(db, piar, request)
    db.commit()
    db.refresh(piar)
    return ApiResponse(success=True, message="Need added successfully", data=to_response(piar))


@router.put("/{piar_id}/needs/{special_need_id}/deactivate", response_model=ApiResponse[PiarResponse])
def remove_need(piar_id: int, special_need_id: int, db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "editar"))):
    piar = find_piar_or_404(db, piar_id)
    check_student_access(db, access, piar.student_id)
    require_consent_for_teachers(access, piar)
    pn = db.query(PiarNeed).filter(
        PiarNeed.piar_id == piar.id, PiarNeed.special_need_id == special_need_id, PiarNeed.estado.is_(True)
    ).first()
    if pn is None:
        raise ResourceNotFoundException("That need is not registered in the PIAR")
    pn.estado = False
    db.commit()
    db.refresh(piar)
    return ApiResponse(success=True, message="Need removed successfully", data=to_response(piar))
