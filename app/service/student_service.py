from typing import List

from fastapi import Depends

from app.dto.request.student import CreateStudentRequest, UpdateStudentRequest
from app.dto.response.student import StudentResponse
from app.exception import ResourceNotFoundException
from app.model import Student, User, UserRole
from app.repository.student_repository import StudentRepository
from app.repository.teacher_repository import TeacherRepository
from app.service.user_service import UserService


class StudentService:

    def __init__(
        self,
        student_repository: StudentRepository = Depends(),
        user_service: UserService = Depends(),
        teacher_repository: TeacherRepository = Depends(),
    ):
        self.teacher_repository = teacher_repository
        self.student_repository = student_repository
        self.user_service = user_service

    @staticmethod
    def to_response(s: Student) -> StudentResponse:
        return StudentResponse(
            id=s.id, user_id=s.user.id, document=s.user.document, full_name=s.user.full_name,
            email=s.user.email, phone=s.user.phone, birth_date=s.user.birth_date, enabled=s.user.enabled,
            document_type=s.user.document_type, gender=s.user.gender, address=s.user.address,
            estado=s.estado, creado=s.creado, actualizado=s.actualizado,
            guardian_name=s.guardian_name, guardian_phone=s.guardian_phone, guardian_email=s.guardian_email,
        )

    def find_or_404(self, student_id: int) -> Student:
        s = self.student_repository.find_active_by_id(student_id)
        if s is None:
            raise ResourceNotFoundException(f"Student with id {student_id} not found")
        return s

    def create_student(self, request: CreateStudentRequest) -> StudentResponse:
        document = request.document.strip()
        email = request.email.strip().lower()

        self.user_service.assert_identity_available(document, email)
        user = self.user_service.register_user(request, UserRole.STUDENT, document, email)

        student = Student(
            user_id=user.id, guardian_name=request.guardian_name.strip(),
            guardian_phone=request.guardian_phone.strip(), guardian_email=request.guardian_email.strip(),
        )
        self.student_repository.add(student)
        self.student_repository.commit()
        self.student_repository.refresh(student)
        return self.to_response(student)

    def get_all_students(self) -> List[StudentResponse]:
        return [self.to_response(s) for s in self.student_repository.find_all_active()]

    def get_student_by_id(self, student_id: int) -> StudentResponse:
        return self.to_response(self.find_or_404(student_id))

    def update_student(self, student_id: int, request: UpdateStudentRequest) -> StudentResponse:
        student = self.find_or_404(student_id)
        student.guardian_name = request.guardian_name.strip()
        student.guardian_phone = request.guardian_phone.strip()
        student.guardian_email = request.guardian_email.strip()
        self.student_repository.commit()
        self.student_repository.refresh(student)
        return self.to_response(student)

    def get_visible_students(self, current_user: User) -> List[StudentResponse]:
        """Directivos: todos los estudiantes. Docente: solo los matriculados en los cursos donde dicta clase."""
        if current_user.role_ref.nombre == "TEACHER":
            teacher = self.teacher_repository.find_active_by_user_id(current_user.id)
            items = [] if teacher is None else self.student_repository.find_active_by_teacher(teacher.id)
            return [self.to_response(s) for s in items]
        return self.get_all_students()
