from typing import List, Optional, Set

from app.model import CourseSubject, Enrollment, EnrollmentStatus
from app.repository.base_repository import BaseRepository


class CourseSubjectRepository(BaseRepository):

    def exists_active_by_id_and_teacher(self, course_subject_id: int, teacher_id: int) -> bool:
        """¿La materia-curso está activa y asignada a este docente?"""
        return self.db.query(CourseSubject.id).filter(
            CourseSubject.id == course_subject_id,
            CourseSubject.teacher_id == teacher_id,
            CourseSubject.estado.is_(True),
        ).first() is not None

    def teacher_teaches_student(self, teacher_id: int, student_id: int) -> bool:
        """¿El docente dicta alguna materia en un curso donde el estudiante está matriculado (activo)?"""
        return (
            self.db.query(CourseSubject.id)
            .join(Enrollment, Enrollment.course_id == CourseSubject.course_id)
            .filter(
                CourseSubject.teacher_id == teacher_id, CourseSubject.estado.is_(True),
                Enrollment.student_id == student_id, Enrollment.status == EnrollmentStatus.ACTIVE,
                Enrollment.estado.is_(True),
            )
            .first()
        ) is not None

    def student_ids_taught_by(self, teacher_id: int) -> Set[int]:
        """Todos los estudiantes (matrícula activa) de los cursos donde el docente dicta clase, en UNA consulta."""
        rows = (
            self.db.query(Enrollment.student_id).distinct()
            .join(CourseSubject, CourseSubject.course_id == Enrollment.course_id)
            .filter(
                CourseSubject.teacher_id == teacher_id, CourseSubject.estado.is_(True),
                Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True),
            )
            .all()
        )
        return {r[0] for r in rows}

    def find_active_by_id(self, cs_id: int) -> Optional[CourseSubject]:
        return self.db.query(CourseSubject).filter(CourseSubject.id == cs_id, CourseSubject.estado.is_(True)).first()

    def find_all_active(self) -> List[CourseSubject]:
        return self.db.query(CourseSubject).filter(CourseSubject.estado.is_(True)).order_by(CourseSubject.id).all()

    def find_active_by_teacher_id(self, teacher_id: int) -> List[CourseSubject]:
        return self.db.query(CourseSubject).filter(
            CourseSubject.teacher_id == teacher_id, CourseSubject.estado.is_(True)
        ).order_by(CourseSubject.id).all()

    def exists_active_by_course_and_subject(self, course_id: int, subject_id: int) -> bool:
        return self.db.query(CourseSubject).filter(
            CourseSubject.course_id == course_id, CourseSubject.subject_id == subject_id,
            CourseSubject.estado.is_(True),
        ).first() is not None

    def exists_active_by_course_and_teacher(self, course_id: int, teacher_id: int) -> bool:
        return self.db.query(CourseSubject).filter(
            CourseSubject.course_id == course_id, CourseSubject.teacher_id == teacher_id,
            CourseSubject.estado.is_(True),
        ).first() is not None

    def find_by_id(self, cs_id: int) -> Optional[CourseSubject]:
        """Busca la materia-curso sin filtrar por estado (el servicio valida si está activa)."""
        return self.db.query(CourseSubject).filter(CourseSubject.id == cs_id).first()

    def find_all_including_inactive(self) -> List[CourseSubject]:
        return self.db.query(CourseSubject).order_by(CourseSubject.estado.desc(), CourseSubject.id).all()
