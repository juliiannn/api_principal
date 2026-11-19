"""Módulo de reportes: genera Excel o PDF según los filtros, los guarda de forma TEMPORAL (REPORT_TTL_HOURS),
permite descargarlos y los envía al correo del usuario que los pide."""
import os
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.access import Access
from app.config.database import SessionLocal, get_db
from app.config.settings import settings
from app.dto.request.report import ReportEmailRequest, ReportFiltersRequest, ReportRequest
from app.dto.response.report import (
    ReportCatalogItem, ReportEmailResponse, ReportFileResponse, ReportOption, ReportOptionsResponse,
)
from app.exception import ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException
from app.model import (
    Course, CourseSubject, Enrollment, EnrollmentStatus, NotificationEvent, PermissionScope, ReportFile, Subject, User,
)
from app.repository.notification_repository import ReportFileRepository
from app.repository.student_repository import StudentRepository
from app.repository.teacher_repository import TeacherRepository
from app.service import report_exporter
from app.service.notification_service import NotificationService
from app.service.report_builder import CATALOG, CATALOG_BY_TYPE, ReportBuilder, ReportData, ReportFilters, Viewer

MIME = {"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "pdf": "application/pdf"}


def cleanup_expired_reports() -> int:
    """Borra del disco los reportes vencidos y los marca inactivos (al iniciar la API y en cada generación)."""
    db = SessionLocal()
    try:
        return _cleanup(db)
    finally:
        db.close()


def _cleanup(db: Session) -> int:
    now = datetime.now()
    expired = db.query(ReportFile).filter(ReportFile.estado.is_(True), ReportFile.expira_en <= now).all()
    for rf in expired:
        try:
            if os.path.exists(rf.ruta):
                os.remove(rf.ruta)
        except OSError:
            pass
        rf.estado = False
    db.commit()
    return len(expired)


class ReportService:

    def __init__(
        self,
        db: Session = Depends(get_db),
        report_file_repository: ReportFileRepository = Depends(),
        teacher_repository: TeacherRepository = Depends(),
        student_repository: StudentRepository = Depends(),
        notification_service: NotificationService = Depends(),
    ):
        self.db = db
        self.files = report_file_repository
        self.teachers = teacher_repository
        self.students = student_repository
        self.notifier = notification_service

    # ---------- catálogo ----------

    def catalog(self, access: Access) -> List[ReportCatalogItem]:
        return [ReportCatalogItem(tipo=t, titulo=title, descripcion=desc,
                                  filtros=[f for f in filters if not (access.scope == PermissionScope.OWN and f == "curso")])
                for t, title, desc, filters, scopes in CATALOG if access.scope in scopes]

    def options(self, access: Access) -> ReportOptionsResponse:
        """Cursos y materias para los filtros: todos (directivos), los que dicta (docente) o los suyos (estudiante)."""
        viewer = self._viewer(access)
        if viewer.scope == PermissionScope.ALL:
            courses = self.db.query(Course).filter(Course.estado.is_(True)).all()
            subjects = self.db.query(Subject).filter(Subject.estado.is_(True)).all()
        else:
            q = self.db.query(CourseSubject).filter(CourseSubject.estado.is_(True))
            if viewer.teacher is not None:
                q = q.filter(CourseSubject.teacher_id == viewer.teacher.id)
            else:
                course_ids = [e.course_id for e in self.db.query(Enrollment).filter(
                    Enrollment.student_id == viewer.student.id, Enrollment.status == EnrollmentStatus.ACTIVE,
                    Enrollment.estado.is_(True)).all()]
                q = q.filter(CourseSubject.course_id.in_(course_ids or [-1]))
            rows = q.all()
            courses = [] if viewer.student is not None else list({cs.course.id: cs.course for cs in rows}.values())
            subjects = list({cs.subject.id: cs.subject for cs in rows}.values())
        return ReportOptionsResponse(
            cursos=[ReportOption(id=c.id, nombre=c.name) for c in courses],
            materias=sorted((ReportOption(id=s.id, nombre=s.name) for s in subjects), key=lambda o: o.nombre),
        )

    # ---------- generar ----------

    def _viewer(self, access: Access) -> Viewer:
        if access.scope == PermissionScope.ASSIGNED:
            teacher = self.teachers.find_active_by_user_id(access.user.id)
            if teacher is None:
                raise ForbiddenOperationException("Only teachers can generate reports of their courses")
            return Viewer(scope=access.scope, teacher=teacher)
        if access.scope == PermissionScope.OWN:
            student = self.students.find_active_by_user_id(access.user.id)
            if student is None:
                raise ForbiddenOperationException("Only students can generate their own reports")
            return Viewer(scope=access.scope, student=student)
        return Viewer(scope=PermissionScope.ALL)

    def _data(self, tipo: str, filters: ReportFiltersRequest, access: Access) -> ReportData:
        entry = CATALOG_BY_TYPE.get(tipo)
        if entry is None or access.scope not in entry[4]:
            raise ForbiddenOperationException("This report is not available for your role")
        if filters.desde and filters.hasta and filters.desde > filters.hasta:
            raise InvalidRequestException("End date must not be before start date")
        viewer = self._viewer(access)
        f = ReportFilters(curso_id=None if viewer.scope == PermissionScope.OWN else filters.curso_id,
                          materia_id=filters.materia_id, periodo=filters.periodo,
                          desde=filters.desde, hasta=filters.hasta)
        builder = ReportBuilder(self.db, viewer, f, settings.REPORT_MAX_ROWS)
        if viewer.scope == PermissionScope.ASSIGNED and f.curso_id and f.curso_id not in builder._teacher_course_ids():
            raise ForbiddenOperationException("You can only generate reports of courses where you teach")
        return builder.build(tipo)

    def _store(self, data: ReportData, formato: str, user: User) -> ReportFile:
        content = report_exporter.to_xlsx(data, user.full_name) if formato == "xlsx" else report_exporter.to_pdf(data, user.full_name)
        os.makedirs(settings.REPORTS_DIR, exist_ok=True)
        disk_name = f"{uuid.uuid4().hex}.{formato}"          # nombre aleatorio: no se puede adivinar ni recorrer
        path = os.path.join(settings.REPORTS_DIR, disk_name)
        with open(path, "wb") as fh:
            fh.write(content)
        now = datetime.now()
        rf = ReportFile(
            usuario_id=user.id, tipo=data.tipo, formato=formato, titulo=data.titulo, filtros=data.filtros,
            nombre_archivo=f"{data.tipo}_{now:%Y%m%d_%H%M%S}.{formato}", ruta=path, tamano_bytes=len(content),
            filas=len(data.rows), expira_en=now + timedelta(hours=settings.REPORT_TTL_HOURS),
        )
        return self.files.save(rf)

    def generate(self, request: ReportRequest, access: Access) -> ReportFileResponse:
        _cleanup(self.db)
        data = self._data(request.tipo, request, access)
        return self.to_response(self._store(data, request.formato, access.user))

    def send_by_email(self, request: ReportEmailRequest, access: Access) -> ReportEmailResponse:
        """Genera el reporte en los formatos pedidos y lo envía al correo REGISTRADO del usuario."""
        _cleanup(self.db)
        data = self._data(request.tipo, request, access)
        files = [self._store(data, fmt, access.user) for fmt in dict.fromkeys(request.formatos)]
        user = access.user
        cuerpo = (f"Hola, {user.full_name}.\n\n"
                  f"Adjuntamos el reporte “{data.titulo}” que solicitaste ({', '.join(f.formato.upper() for f in files)}).\n\n"
                  f"Filtros: {data.filtros}\n\n"
                  + "\n".join(f"{label}: {value}" for label, value in data.summary) +
                  f"\n\nTambién puedes descargarlo desde la plataforma durante {settings.REPORT_TTL_HOURS} horas.")
        n = self.notifier.send_now(NotificationEvent.REPORT_GENERATED, user.email, f"Reporte: {data.titulo}", cuerpo,
                                   user.id, [f.id for f in files])
        if n.estado_envio == "ENVIADO":
            for f in files:
                f.enviado_a = user.email
            self.db.commit()
        return ReportEmailResponse(estado=n.estado_envio, destinatario=user.email, enviado_a=n.enviado_a, error=n.error,
                                   archivos=[self.to_response(f) for f in files])

    # ---------- historial y descarga ----------

    def my_files(self, access: Access) -> List[ReportFileResponse]:
        return [self.to_response(f) for f in self.files.find_recent_by_user(access.user.id, datetime.now())]

    def file_for_download(self, file_id: int, access: Access) -> ReportFile:
        rf = self.files.find_by_id(file_id)
        if rf is None or rf.expira_en <= datetime.now() or not os.path.exists(rf.ruta):
            raise ResourceNotFoundException("The report expired or does not exist; generate it again")
        if rf.usuario_id != access.user.id:
            raise ForbiddenOperationException("You can only download your own reports")
        return rf

    @staticmethod
    def to_response(rf: ReportFile) -> ReportFileResponse:
        return ReportFileResponse(
            id=rf.id, tipo=rf.tipo, titulo=rf.titulo, formato=rf.formato, filtros=rf.filtros,
            nombre_archivo=rf.nombre_archivo, tamano_bytes=rf.tamano_bytes, filas=rf.filas, creado=rf.creado,
            expira_en=rf.expira_en, enviado_a=rf.enviado_a,
        )
