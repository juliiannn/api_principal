from sqlalchemy.orm import Session

from app.exceptions import ForbiddenOperationException, InvalidRequestException
from app.models import CourseSubject, Enrollment, EnrollmentStatus, Role, Teacher, User, UserRole


def get_role_id(db: Session, role: UserRole) -> int:
    """Devuelve el id del rol (tabla roles) a partir de su nombre. Se usa al crear usuarios."""
    found = db.query(Role).filter(Role.nombre == role.value, Role.estado.is_(True)).first()
    if found is None:
        raise InvalidRequestException(f"El rol {role.value} no existe o está inactivo")
    return found.id


def _find_teacher(db: Session, user: User):
    return db.query(Teacher).filter(Teacher.user_id == user.id, Teacher.estado.is_(True)).first()


def ensure_teacher_teaches_course_subject(db: Session, user: User, course_subject_id: int):
    """El docente solo puede acceder a materias que tiene asignadas."""
    teacher = _find_teacher(db, user)
    found = None
    if teacher is not None:
        found = db.query(CourseSubject.id).filter(
            CourseSubject.id == course_subject_id, CourseSubject.teacher_id == teacher.id, CourseSubject.estado.is_(True)
        ).first()
    if found is None:
        raise ForbiddenOperationException("You can only access subjects assigned to you")


def ensure_teacher_teaches_student(db: Session, user: User, student_id: int):
    """El docente solo puede acceder a estudiantes matriculados en cursos donde dicta clase."""
    teacher = _find_teacher(db, user)
    found = None
    if teacher is not None:
        found = (
            db.query(CourseSubject.id)
            .join(Enrollment, Enrollment.course_id == CourseSubject.course_id)
            .filter(
                CourseSubject.teacher_id == teacher.id, CourseSubject.estado.is_(True),
                Enrollment.student_id == student_id, Enrollment.status == EnrollmentStatus.ACTIVE,
                Enrollment.estado.is_(True),
            )
            .first()
        )
    if found is None:
        raise ForbiddenOperationException("You can only access students from courses where you teach")
