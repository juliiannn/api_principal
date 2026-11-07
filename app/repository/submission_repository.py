from typing import List, Optional

from app.model import Assignment, CourseSubject, Submission
from app.repository.base_repository import BaseRepository


class SubmissionRepository(BaseRepository):

    def find_active_by_id(self, submission_id: int) -> Optional[Submission]:
        return self.db.query(Submission).filter(Submission.id == submission_id, Submission.estado.is_(True)).first()

    def exists_active_by_assignment_and_student(self, assignment_id: int, student_id: int) -> bool:
        return self.db.query(Submission).filter(
            Submission.assignment_id == assignment_id, Submission.student_id == student_id,
            Submission.estado.is_(True),
        ).first() is not None

    def find_active_by_student(self, student_id: int) -> List[Submission]:
        return (
            self.db.query(Submission)
            .filter(Submission.student_id == student_id, Submission.estado.is_(True))
            .order_by(Submission.creado.desc()).all()
        )

    def find_active_by_assignment(self, assignment_id: int) -> List[Submission]:
        return (
            self.db.query(Submission)
            .filter(Submission.assignment_id == assignment_id, Submission.estado.is_(True))
            .order_by(Submission.creado.desc()).all()
        )

    def find_active_by_teacher(self, teacher_id: int, only_pending: bool = False) -> List[Submission]:
        """Entregas de las tareas de las materias que dicta el docente (opcionalmente solo las sin calificar)."""
        q = (
            self.db.query(Submission)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(CourseSubject, Assignment.course_subject_id == CourseSubject.id)
            .filter(CourseSubject.teacher_id == teacher_id, Submission.estado.is_(True),
                    Assignment.estado.is_(True))
        )
        if only_pending:
            q = q.filter(Submission.nota.is_(None))
        return q.order_by(Submission.creado.desc()).all()

    def find_all_active(self) -> List[Submission]:
        return self.db.query(Submission).filter(Submission.estado.is_(True)).order_by(Submission.creado.desc()).all()
