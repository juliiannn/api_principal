from typing import List, Optional

from fastapi import Depends

from app.exception import ForbiddenOperationException
from app.model import RoleModule, Student, Teacher, User
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.role_module_repository import RoleModuleRepository
from app.repository.student_repository import StudentRepository
from app.repository.teacher_repository import TeacherRepository


class CurrentUserService:
    """Operaciones sobre el usuario autenticado: perfiles, permisos y alcance de un docente."""

    def __init__(
        self,
        teacher_repository: TeacherRepository = Depends(),
        student_repository: StudentRepository = Depends(),
        course_subject_repository: CourseSubjectRepository = Depends(),
        role_module_repository: RoleModuleRepository = Depends(),
    ):
        self.teacher_repository = teacher_repository
        self.student_repository = student_repository
        self.course_subject_repository = course_subject_repository
        self.role_module_repository = role_module_repository

    def find_teacher(self, user: User) -> Optional[Teacher]:
        return self.teacher_repository.find_active_by_user_id(user.id)

    def find_student(self, user: User) -> Optional[Student]:
        return self.student_repository.find_active_by_user_id(user.id)

    def get_user_permissions(self, user: User) -> List[RoleModule]:
        """Todos los permisos activos del rol del usuario (para el endpoint que arma el menú)."""
        return self.role_module_repository.find_active_by_role(user.role_id)

    def ensure_teacher_teaches_course_subject(self, user: User, course_subject_id: int) -> None:
        """El docente solo puede acceder a materias que tiene asignadas."""
        teacher = self.find_teacher(user)
        allowed = teacher is not None and self.course_subject_repository.exists_active_by_id_and_teacher(
            course_subject_id, teacher.id
        )
        if not allowed:
            raise ForbiddenOperationException("You can only access subjects assigned to you")

    def ensure_teacher_teaches_student(self, user: User, student_id: int) -> None:
        """El docente solo puede acceder a estudiantes matriculados en cursos donde dicta clase."""
        teacher = self.find_teacher(user)
        allowed = teacher is not None and self.course_subject_repository.teacher_teaches_student(
            teacher.id, student_id
        )
        if not allowed:
            raise ForbiddenOperationException("You can only access students from courses where you teach")
