from typing import List

from fastapi import Depends

from app.dto.request.assignment import CreateAssignmentRequest, UpdateAssignmentRequest
from app.dto.response.assignment import AssignmentResponse
from app.exception import ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException
from app.model import Assignment, Student, Teacher, User
from app.repository.assignment_repository import AssignmentRepository
from app.repository.course_subject_repository import CourseSubjectRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.service.current_user_service import CurrentUserService


class AssignmentService:

    def __init__(
        self,
        assignment_repository: AssignmentRepository = Depends(),
        course_subject_repository: CourseSubjectRepository = Depends(),
        enrollment_repository: EnrollmentRepository = Depends(),
        current_user_service: CurrentUserService = Depends(),
    ):
        self.assignment_repository = assignment_repository
        self.course_subject_repository = course_subject_repository
        self.enrollment_repository = enrollment_repository
        self.current_user_service = current_user_service

    @staticmethod
    def to_response(a: Assignment) -> AssignmentResponse:
        cs = a.course_subject
        return AssignmentResponse(
            id=a.id, course_subject_id=cs.id, course_id=cs.course_id, course_name=cs.course.name,
            subject_id=cs.subject_id, subject_name=cs.subject.name, teacher_name=cs.teacher.user.full_name,
            title=a.title, description=a.description, due_date=a.due_date, estado=a.estado, creado=a.creado,
        )

    def create_assignment(self, request: CreateAssignmentRequest, current_teacher: Teacher) -> AssignmentResponse:
        cs = self.course_subject_repository.find_by_id(request.course_subject_id)
        if cs is None:
            raise ResourceNotFoundException(f"CourseSubject with id {request.course_subject_id} not found")
        if cs.teacher_id != current_teacher.id:
            raise ForbiddenOperationException("You can only publish assignments for subjects assigned to you")
        if not cs.estado:
            raise InvalidRequestException("Cannot publish an assignment for an inactive course-subject assignment")

        assignment = Assignment(
            course_subject_id=cs.id, title=request.title.strip(),
            description=request.description.strip(), due_date=request.due_date,
        )
        return self.to_response(self.assignment_repository.save(assignment))

    def get_my_assignments(self, current_student: Student) -> List[AssignmentResponse]:
        enrollment = self.enrollment_repository.find_current_by_student(current_student.id)
        if enrollment is None:
            raise ResourceNotFoundException("You are not actively enrolled in any course")
        return [self.to_response(a) for a in self.assignment_repository.find_active_by_course(enrollment.course_id)]

    def get_assignments_by_course_subject(self, cs_id: int, current_user: User) -> List[AssignmentResponse]:
        if current_user.role_ref.nombre == "TEACHER":
            self.current_user_service.ensure_teacher_teaches_course_subject(current_user, cs_id)
        return [self.to_response(a) for a in self.assignment_repository.find_active_by_course_subject(cs_id)]

    def _find_owned_or_raise(self, assignment_id: int, current_teacher: Teacher) -> Assignment:
        assignment = self.assignment_repository.find_active_by_id(assignment_id)
        if assignment is None:
            raise ResourceNotFoundException(f"Assignment with id {assignment_id} not found")
        if assignment.course_subject.teacher_id != current_teacher.id:
            raise ForbiddenOperationException("You can only manage assignments for subjects assigned to you")
        return assignment

    def get_my_teaching_assignments(self, current_teacher: Teacher) -> List[AssignmentResponse]:
        items = self.assignment_repository.find_active_by_teacher(current_teacher.id)
        return [self.to_response(a) for a in items]

    def update_assignment(
        self, assignment_id: int, request: UpdateAssignmentRequest, current_teacher: Teacher
    ) -> AssignmentResponse:
        assignment = self._find_owned_or_raise(assignment_id, current_teacher)
        assignment.title = request.title.strip()
        assignment.description = request.description.strip()
        assignment.due_date = request.due_date
        self.assignment_repository.commit()
        self.assignment_repository.refresh(assignment)
        return self.to_response(assignment)

    def deactivate_assignment(self, assignment_id: int, current_teacher: Teacher) -> AssignmentResponse:
        assignment = self._find_owned_or_raise(assignment_id, current_teacher)
        assignment.estado = False
        self.assignment_repository.commit()
        self.assignment_repository.refresh(assignment)
        return self.to_response(assignment)

    def _teacher_scope(self, current_user: User):
        """None = ve todo (personal directivo); Teacher = solo lo de sus materias."""
        if current_user.role_ref.nombre != "TEACHER":
            return None
        teacher = self.current_user_service.find_teacher(current_user)
        if teacher is None:
            raise ForbiddenOperationException("No teacher profile found for the authenticated user")
        return teacher

    def get_all_assignments(self, current_user: User) -> List[AssignmentResponse]:
        """Listado general: directivos ven todas las tareas; el docente, las de sus materias."""
        teacher = self._teacher_scope(current_user)
        items = self.assignment_repository.find_all_active() if teacher is None \
            else self.assignment_repository.find_active_by_teacher(teacher.id)
        return [self.to_response(a) for a in items]
