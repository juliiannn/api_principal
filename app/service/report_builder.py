"""Datos de cada reporte, ya filtrados y respetando el alcance del rol (tabla role_modules):
  ALL      → directivos: todo el colegio
  ASSIGNED → docente: solo sus cursos y sus materias
  OWN      → estudiante: solo su información
El resultado (ReportData) es independiente del formato: el exportador lo convierte en Excel o PDF."""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.model import (
    Attendance, AttendanceStatus, Course, CourseSubject, Enrollment, EnrollmentStatus, Grade, PermissionScope, Piar,
    Student, Subject, Teacher,
)

PERIOD_LABEL = {"PERIOD_1": "Periodo 1", "PERIOD_2": "Periodo 2", "PERIOD_3": "Periodo 3", "PERIOD_4": "Periodo 4"}
STATUS_LABEL = {"PRESENT": "Presente", "ABSENT": "Ausente", "LATE": "Tarde"}


@dataclass
class ReportColumn:
    header: str
    width: int = 14                  # ancho aproximado en caracteres
    kind: str = "text"               # text | number | decimal | percent | date
    alert_below: Optional[float] = None   # resalta en rojo los valores menores (notas bajas)


@dataclass
class ReportData:
    tipo: str
    titulo: str
    filtros: str                     # filtros aplicados, en texto
    columns: List[ReportColumn]
    rows: List[list]
    summary: List[tuple] = field(default_factory=list)   # [(indicador, valor)]
    landscape: bool = False
    truncated: bool = False


@dataclass
class ReportFilters:
    curso_id: Optional[int] = None
    materia_id: Optional[int] = None
    periodo: Optional[str] = None
    desde: Optional[date] = None
    hasta: Optional[date] = None


@dataclass
class Viewer:
    """Quién pide el reporte y con qué alcance."""
    scope: PermissionScope
    teacher: Optional[Teacher] = None
    student: Optional[Student] = None


# Reportes disponibles: (tipo, título, descripción, filtros, alcances permitidos)
CATALOG = [
    ("consolidado", "Consolidado académico", "Promedio general, materias en bajo, faltas y nivel de cada estudiante.",
     ["curso", "periodo"], {PermissionScope.ALL, PermissionScope.ASSIGNED, PermissionScope.OWN}),
    ("notas", "Notas por estudiante", "Cada nota registrada con su materia, docente y periodo.",
     ["curso", "materia", "periodo"], {PermissionScope.ALL, PermissionScope.ASSIGNED, PermissionScope.OWN}),
    ("asistencia", "Asistencia", "Registros de asistencia por clase en un rango de fechas.",
     ["curso", "materia", "desde", "hasta"], {PermissionScope.ALL, PermissionScope.ASSIGNED, PermissionScope.OWN}),
    ("estudiantes", "Estudiantes y acudientes", "Listado de estudiantes matriculados con los datos de su acudiente.",
     ["curso"], {PermissionScope.ALL, PermissionScope.ASSIGNED}),
    ("piar", "Estudiantes con PIAR", "PIAR activos con su necesidad educativa, metas y ajustes razonables.",
     ["curso"], {PermissionScope.ALL, PermissionScope.ASSIGNED}),
]
CATALOG_BY_TYPE = {c[0]: c for c in CATALOG}


def level_of(avg: float) -> str:
    return "Superior" if avg >= 9.5 else "Alto" if avg >= 8 else "Básico" if avg >= 6 else "Bajo"


def fmt_date(d) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


class ReportBuilder:

    def __init__(self, db: Session, viewer: Viewer, filters: ReportFilters, max_rows: int):
        self.db = db
        self.viewer = viewer
        self.f = filters
        self.max_rows = max_rows

    # ---------- alcance ----------

    def _teacher_cs_ids(self) -> Set[int]:
        rows = self.db.query(CourseSubject.id).filter(
            CourseSubject.teacher_id == self.viewer.teacher.id, CourseSubject.estado.is_(True)).all()
        return {r[0] for r in rows}

    def _teacher_course_ids(self) -> Set[int]:
        rows = self.db.query(CourseSubject.course_id).filter(
            CourseSubject.teacher_id == self.viewer.teacher.id, CourseSubject.estado.is_(True)).all()
        return {r[0] for r in rows}

    def _active_enrollments(self) -> List[Enrollment]:
        q = self.db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True))
        if self.f.curso_id:
            q = q.filter(Enrollment.course_id == self.f.curso_id)
        if self.viewer.scope == PermissionScope.ASSIGNED:
            q = q.filter(Enrollment.course_id.in_(self._teacher_course_ids() or {-1}))
        if self.viewer.scope == PermissionScope.OWN:
            q = q.filter(Enrollment.student_id == self.viewer.student.id)
        return q.order_by(Enrollment.course_id).all()

    def _cs_filter(self, q, model):
        """Aplica curso, materia y alcance a una consulta de Grade o Attendance."""
        q = q.join(CourseSubject, CourseSubject.id == model.course_subject_id)
        if self.f.curso_id:
            q = q.filter(CourseSubject.course_id == self.f.curso_id)
        if self.f.materia_id:
            q = q.filter(CourseSubject.subject_id == self.f.materia_id)
        if self.viewer.scope == PermissionScope.ASSIGNED:
            q = q.filter(CourseSubject.teacher_id == self.viewer.teacher.id)
        if self.viewer.scope == PermissionScope.OWN:
            q = q.filter(model.student_id == self.viewer.student.id)
        return q

    # ---------- texto de filtros ----------

    def describe(self) -> str:
        parts = []
        if self.f.curso_id:
            c = self.db.query(Course).filter(Course.id == self.f.curso_id).first()
            parts.append(f"Curso: {c.name if c else self.f.curso_id}")
        else:
            parts.append("Curso: todos" if self.viewer.scope == PermissionScope.ALL else
                         "Curso: mis cursos" if self.viewer.scope == PermissionScope.ASSIGNED else "Curso: el mío")
        if self.f.materia_id:
            s = self.db.query(Subject).filter(Subject.id == self.f.materia_id).first()
            parts.append(f"Materia: {s.name if s else self.f.materia_id}")
        if self.f.periodo:
            parts.append(PERIOD_LABEL.get(self.f.periodo, self.f.periodo))
        if self.f.desde or self.f.hasta:
            parts.append(f"Fechas: {fmt_date(self.f.desde) or 'inicio'} a {fmt_date(self.f.hasta) or 'hoy'}")
        if self.viewer.scope == PermissionScope.OWN and self.viewer.student:
            parts.append(f"Estudiante: {self.viewer.student.user.full_name}")
        return " · ".join(parts)

    def _limit(self, rows: list) -> tuple[list, bool]:
        return (rows[: self.max_rows], True) if len(rows) > self.max_rows else (rows, False)

    # ---------- reportes ----------

    def build(self, tipo: str) -> ReportData:
        return getattr(self, f"_{tipo}")()

    def _notas(self) -> ReportData:
        q = self._cs_filter(self.db.query(Grade), Grade)
        if self.f.periodo:
            q = q.filter(Grade.period == self.f.periodo)
        grades = q.order_by(CourseSubject.course_id, Grade.student_id, CourseSubject.subject_id, Grade.period).all()
        rows = [[g.course_subject.course.name, g.student.user.full_name, g.student.user.document,
                 g.course_subject.subject.name, g.course_subject.teacher.user.full_name,
                 PERIOD_LABEL.get(g.period.value, g.period.value), float(g.value), level_of(float(g.value))]
                for g in grades]
        rows, cut = self._limit(rows)
        values = [r[6] for r in rows]
        avg = sum(values) / len(values) if values else 0
        return ReportData(
            tipo="notas", titulo="Notas por estudiante", filtros=self.describe(), truncated=cut, landscape=True,
            columns=[ReportColumn("Curso", 12), ReportColumn("Estudiante", 30), ReportColumn("Documento", 14),
                     ReportColumn("Materia", 18), ReportColumn("Docente", 28), ReportColumn("Periodo", 11),
                     ReportColumn("Nota", 8, "decimal", alert_below=6), ReportColumn("Desempeño", 11)],
            rows=rows,
            summary=[("Notas", len(values)), ("Promedio", f"{avg:.1f}" if values else "—"),
                     ("Notas menores a 6.0", sum(1 for v in values if v < 6)),
                     ("Estudiantes", len({r[2] for r in rows}))],
        )

    def _asistencia(self) -> ReportData:
        q = self._cs_filter(self.db.query(Attendance), Attendance)
        if self.f.desde:
            q = q.filter(Attendance.date >= self.f.desde)
        if self.f.hasta:
            q = q.filter(Attendance.date <= self.f.hasta)
        records = q.order_by(Attendance.date.desc(), CourseSubject.course_id, Attendance.student_id).all()
        rows = [[a.date, a.course_subject.course.name, a.student.user.full_name, a.course_subject.subject.name,
                 STATUS_LABEL.get(a.status.value, a.status.value)] for a in records]
        rows, cut = self._limit(rows)
        total = len(rows)
        absent = sum(1 for r in rows if r[4] == "Ausente")
        late = sum(1 for r in rows if r[4] == "Tarde")
        return ReportData(
            tipo="asistencia", titulo="Asistencia", filtros=self.describe(), truncated=cut,
            columns=[ReportColumn("Fecha", 11, "date"), ReportColumn("Curso", 12), ReportColumn("Estudiante", 30),
                     ReportColumn("Materia", 18), ReportColumn("Estado", 10)],
            rows=rows,
            summary=[("Registros", total), ("Ausencias", absent), ("Llegadas tarde", late),
                     ("Asistencia", f"{(total - absent) / total * 100:.1f}%" if total else "—")],
        )

    def _consolidado(self) -> ReportData:
        enrollments = self._active_enrollments()
        student_ids = [e.student_id for e in enrollments]
        gq = self._cs_filter(self.db.query(Grade), Grade).filter(Grade.student_id.in_(student_ids or [-1]))
        if self.f.periodo:
            gq = gq.filter(Grade.period == self.f.periodo)
        by_student: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        for g in gq.all():
            by_student[g.student_id][g.course_subject.subject.name].append(float(g.value))
        aq = self._cs_filter(self.db.query(Attendance), Attendance).filter(Attendance.student_id.in_(student_ids or [-1]))
        att: Dict[int, List[int]] = defaultdict(lambda: [0, 0])     # [registros, ausencias]
        for a in aq.all():
            att[a.student_id][0] += 1
            att[a.student_id][1] += 1 if a.status == AttendanceStatus.ABSENT else 0
        with_piar = {p.student_id for p in self.db.query(Piar).filter(Piar.estado.is_(True)).all()}

        rows = []
        for e in enrollments:
            subjects = by_student.get(e.student_id, {})
            avgs = {name: sum(v) / len(v) for name, v in subjects.items()}
            general = sum(avgs.values()) / len(avgs) if avgs else None
            low = sorted(f"{n} ({a:.1f})" for n, a in avgs.items() if a < 6)
            total, absent = att.get(e.student_id, [0, 0])
            rows.append([e.course.name, e.student.user.full_name, e.student.user.document,
                         round(general, 1) if general is not None else None,
                         level_of(general) if general is not None else "Sin notas",
                         len(low), ", ".join(low) or "—", absent,
                         (total - absent) / total if total else None,
                         "Sí" if e.student_id in with_piar else "No"])
        rows, cut = self._limit(rows)
        generals = [r[3] for r in rows if r[3] is not None]
        return ReportData(
            tipo="consolidado", titulo="Consolidado académico", filtros=self.describe(), truncated=cut, landscape=True,
            columns=[ReportColumn("Curso", 11), ReportColumn("Estudiante", 28), ReportColumn("Documento", 13),
                     ReportColumn("Promedio", 9, "decimal", alert_below=6), ReportColumn("Desempeño", 11),
                     ReportColumn("Materias en bajo", 9, "number"), ReportColumn("Detalle materias en bajo", 34),
                     ReportColumn("Faltas", 7, "number"), ReportColumn("Asistencia", 10, "percent"),
                     ReportColumn("PIAR", 6)],
            rows=rows,
            summary=[("Estudiantes", len(rows)),
                     ("Promedio del grupo", f"{sum(generals) / len(generals):.1f}" if generals else "—"),
                     ("Estudiantes en riesgo (promedio < 6)", sum(1 for g in generals if g < 6)),
                     ("Estudiantes con PIAR", sum(1 for r in rows if r[9] == "Sí"))],
        )

    def _estudiantes(self) -> ReportData:
        enrollments = self._active_enrollments()
        rows = [[e.course.name, e.student.user.full_name, e.student.user.document_type.value, e.student.user.document,
                 e.student.user.email, e.student.user.phone, e.student.guardian_name or "", e.student.guardian_phone or "",
                 e.student.guardian_email or "", e.enrollment_date] for e in enrollments]
        rows, cut = self._limit(rows)
        return ReportData(
            tipo="estudiantes", titulo="Estudiantes y acudientes", filtros=self.describe(), truncated=cut, landscape=True,
            columns=[ReportColumn("Curso", 11), ReportColumn("Estudiante", 28), ReportColumn("Tipo doc.", 8),
                     ReportColumn("Documento", 13), ReportColumn("Correo", 28), ReportColumn("Teléfono", 12),
                     ReportColumn("Acudiente", 22), ReportColumn("Tel. acudiente", 12), ReportColumn("Correo acudiente", 28),
                     ReportColumn("Matrícula", 11, "date")],
            rows=rows,
            summary=[("Estudiantes", len(rows)), ("Cursos", len({r[0] for r in rows})),
                     ("Sin acudiente registrado", sum(1 for r in rows if not r[6]))],
        )

    def _piar(self) -> ReportData:
        enrollments = {e.student_id: e for e in self._active_enrollments()}
        piars = self.db.query(Piar).filter(Piar.estado.is_(True), Piar.student_id.in_(list(enrollments) or [-1])).all()
        rows = []
        for p in piars:
            needs = ", ".join(n.special_need.nombre for n in p.needs if n.estado)
            rows.append([enrollments[p.student_id].course.name, p.student.user.full_name, needs or "—",
                         "Sí" if p.consentimiento_acudiente else "No",
                         sum(1 for g in p.goals if g.estado), sum(1 for a in p.adjustments if a.estado),
                         p.fecha_inicio, p.observaciones or ""])
        rows.sort(key=lambda r: (r[0], r[1]))
        return ReportData(
            tipo="piar", titulo="Estudiantes con PIAR", filtros=self.describe(), landscape=True,
            columns=[ReportColumn("Curso", 11), ReportColumn("Estudiante", 28), ReportColumn("Necesidad educativa", 28),
                     ReportColumn("Consentimiento", 9), ReportColumn("Metas", 7, "number"), ReportColumn("Ajustes", 7, "number"),
                     ReportColumn("Inicio", 11, "date"), ReportColumn("Observaciones", 40)],
            rows=rows,
            summary=[("PIAR activos", len(rows)), ("Sin consentimiento del acudiente", sum(1 for r in rows if r[3] == "No"))],
        )
