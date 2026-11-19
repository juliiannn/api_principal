from typing import Dict, List, Optional, Tuple

from app.model import Course, Enrollment, EnrollmentStatus
from app.repository.base_repository import BaseRepository


class EnrollmentRepository(BaseRepository):

    def find_active_by_id(self, enrollment_id: int) -> Optional[Enrollment]:
        return self.db.query(Enrollment).filter(Enrollment.id == enrollment_id, Enrollment.estado.is_(True)).first()

    def find_all_active(self) -> List[Enrollment]:
        return self.db.query(Enrollment).filter(Enrollment.estado.is_(True)).order_by(Enrollment.id).all()

    def find_current_by_student(self, student_id: int) -> Optional[Enrollment]:
        """Matrícula vigente (ACTIVE) del estudiante."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id, Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.estado.is_(True),
        ).first()

    def exists_active_in_course(self, student_id: int, course_id: int) -> bool:
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id, Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True),
        ).first() is not None

    def find_active_by_course(self, course_id: int) -> List[Enrollment]:
        return self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id, Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.estado.is_(True),
        ).all()

    def find_all_current(self) -> List[Enrollment]:
        """Todas las matrículas vigentes (ACTIVE y no eliminadas)."""
        return self.db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.ACTIVE, Enrollment.estado.is_(True)
        ).all()

    def find_current_courses(self, student_ids: List[int]) -> Dict[int, Tuple[int, str]]:
        """Curso actual (id, nombre) de varios estudiantes en UNA consulta: {student_id: (course_id, course_name)}."""
        if not student_ids:
            return {}
        rows = (
            self.db.query(Enrollment.student_id, Course.id, Course.name)
            .join(Course, Course.id == Enrollment.course_id)
            .filter(Enrollment.student_id.in_(student_ids), Enrollment.status == EnrollmentStatus.ACTIVE,
                    Enrollment.estado.is_(True))
            .all()
        )
        return {sid: (cid, cname) for sid, cid, cname in rows}

