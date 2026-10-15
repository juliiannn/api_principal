from datetime import date, datetime, time
from decimal import Decimal
from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel, EmailStr, field_validator

from app.models import (
    UserRole, DocumentType, Gender, EnrollmentStatus,
    EducationLevel, ContractType, CoordinationArea, Period,
    AttendanceStatus, DayOfWeek, PermissionScope, AdjustmentType, ProgressLevel,
)

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None


def validate_digits(v: str, field_name: str = "Field") -> str:
    if not v.isdigit():
        raise ValueError(f"{field_name} must contain only numbers")
    return v


def validate_document_format(v: str) -> str:
    if not v.isdigit() or not (6 <= len(v) <= 15):
        raise ValueError("El documento debe tener entre 6 y 15 dígitos numéricos")
    return v


def validate_past_date(v: date) -> date:
    if v >= date.today():
        raise ValueError("La fecha debe ser en el pasado")
    return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    must_change_password: bool
    role: UserRole


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_length(cls, v: str) -> str:
        if not (8 <= len(v) <= 72):
            raise ValueError("La contraseña debe tener entre 8 y 72 caracteres")
        return v


class BasePersonRequest(BaseModel):
    document_type: DocumentType
    document: str
    email: EmailStr
    full_name: str
    phone: str
    birth_date: date
    gender: Gender
    address: str

    @field_validator("document")
    @classmethod
    def _doc(cls, v): return validate_document_format(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v): return validate_digits(v, "Phone")

    @field_validator("birth_date")
    @classmethod
    def _birth(cls, v): return validate_past_date(v)


class CreateUserRequest(BasePersonRequest):
    pass


class UpdateUserRequest(BaseModel):
    document_type: DocumentType
    document: str
    email: EmailStr
    full_name: str
    phone: str
    birth_date: date
    gender: Gender
    address: str


class UserResponse(BaseModel):
    id: int
    document_type: DocumentType
    document: str
    email: str
    full_name: str
    phone: str
    birth_date: date
    gender: Gender
    address: str
    enabled: bool
    must_change_password: bool
    role: UserRole
    estado: bool = True
    creado: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateStudentRequest(BasePersonRequest):
    guardian_name: str
    guardian_phone: str
    guardian_email: EmailStr

    @field_validator("guardian_phone")
    @classmethod
    def _gphone(cls, v): return validate_digits(v, "Guardian phone")


class UpdateStudentRequest(BaseModel):
    guardian_name: str
    guardian_phone: str
    guardian_email: EmailStr

    @field_validator("guardian_phone")
    @classmethod
    def _gphone(cls, v): return validate_digits(v, "Guardian phone")


class StudentResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    guardian_name: str
    guardian_phone: str
    guardian_email: str


class CreateTeacherRequest(BasePersonRequest):
    employee_code: str
    hire_date: date
    profession: str
    specialty: str
    education_level: EducationLevel
    contract_type: ContractType


class UpdateTeacherRequest(BaseModel):
    employee_code: str
    hire_date: date
    profession: str
    specialty: str
    education_level: EducationLevel
    contract_type: ContractType


class TeacherResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    employee_code: str
    hire_date: date
    profession: str
    specialty: str
    education_level: EducationLevel
    contract_type: ContractType


class CreateCoordinatorRequest(BasePersonRequest):
    employee_code: str
    area: CoordinationArea
    assignment_date: date
    education_level: EducationLevel


class UpdateCoordinatorRequest(BaseModel):
    employee_code: str
    area: CoordinationArea
    assignment_date: date
    education_level: EducationLevel


class CoordinatorResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    employee_code: str
    area: CoordinationArea
    assignment_date: date
    education_level: EducationLevel


class CreateRectorRequest(BasePersonRequest):
    employee_code: str
    appointment_date: date
    administrative_period: str
    education_level: EducationLevel


class UpdateRectorRequest(BaseModel):
    employee_code: str
    appointment_date: date
    administrative_period: str
    education_level: EducationLevel


class RectorResponse(BaseModel):
    id: int
    user_id: int
    document: str
    full_name: str
    email: str
    phone: str
    birth_date: date
    enabled: bool
    employee_code: str
    appointment_date: date
    administrative_period: str
    education_level: EducationLevel


class CreateCourseRequest(BaseModel):
    name: str
    grade: str
    classroom: str
    school_year: int
    director_teacher_id: Optional[int] = None


class AssignDirectorTeacherRequest(BaseModel):
    teacher_id: int


class CourseResponse(BaseModel):
    id: int
    name: str
    grade: str
    classroom: str
    school_year: int
    director_teacher_id: Optional[int]
    director_teacher_name: Optional[str]
    estado: bool


class CreateSubjectRequest(BaseModel):
    name: str


class SubjectResponse(BaseModel):
    id: int
    name: str
    estado: bool

    class Config:
        from_attributes = True


class CreateCourseSubjectRequest(BaseModel):
    course_id: int
    subject_id: int
    teacher_id: int


class CourseSubjectResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    teacher_id: int
    teacher_name: str
    estado: bool


class CreateEnrollmentRequest(BaseModel):
    student_id: int
    course_id: int


class UpdateEnrollmentStatusRequest(BaseModel):
    status: EnrollmentStatus


class TransferEnrollmentRequest(BaseModel):
    student_id: int
    new_course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    course_id: int
    course_name: str
    enrollment_date: date
    status: EnrollmentStatus


class CreateGradeRequest(BaseModel):
    student_id: int
    course_subject_id: int
    period: Period
    value: Decimal

    @field_validator("value")
    @classmethod
    def _range(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.0") or v > Decimal("10.0"):
            raise ValueError("Grade must be between 0.0 and 10.0")
        return v


class UpdateGradeRequest(BaseModel):
    value: Decimal

    @field_validator("value")
    @classmethod
    def _range(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.0") or v > Decimal("10.0"):
            raise ValueError("Grade must be between 0.0 and 10.0")
        return v


class GradeResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    course_subject_id: int
    subject_name: str
    course_name: str
    teacher_name: str
    period: Period
    value: Decimal


class CreateAttendanceRequest(BaseModel):
    student_id: int
    course_subject_id: int
    date: date
    status: AttendanceStatus


class BulkAttendanceRecord(BaseModel):
    student_id: int
    status: AttendanceStatus


class CreateBulkAttendanceRequest(BaseModel):
    course_subject_id: int
    date: date
    records: List[BulkAttendanceRecord]


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    course_subject_id: int
    subject_name: str
    course_name: str
    date: date
    status: AttendanceStatus


class CreateScheduleRequest(BaseModel):
    course_subject_id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time


class ScheduleResponse(BaseModel):
    id: int
    course_subject_id: int
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    teacher_id: int
    teacher_name: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time


class CreateAssignmentRequest(BaseModel):
    course_subject_id: int
    title: str
    description: str
    due_date: date


class AssignmentResponse(BaseModel):
    id: int
    course_subject_id: int
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    teacher_name: str
    title: str
    description: str
    due_date: date
    estado: bool = True
    creado: Optional[datetime] = None


class CourseStudentCountResponse(BaseModel):
    course_id: int
    course_name: str
    student_count: int


class SubjectAverageGradeResponse(BaseModel):
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    average_grade: Decimal
    total_grades: int


class CourseAttendanceRateResponse(BaseModel):
    course_id: int
    course_name: str
    attendance_rate: Decimal
    total_records: int


class GeneralStatisticsResponse(BaseModel):
    total_students: int
    total_teachers: int
    total_coordinators: int
    active_courses: int
    total_subjects: int


# ===== Roles, módulos y permisos =====

class CreateRoleRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    estado: bool

    class Config:
        from_attributes = True


class CreateModuleRequest(BaseModel):
    nombre: str
    ruta: str
    descripcion: Optional[str] = None


class ModuleResponse(BaseModel):
    id: int
    nombre: str
    ruta: str
    descripcion: Optional[str]
    estado: bool

    class Config:
        from_attributes = True


class RoleModuleRequest(BaseModel):
    role_id: int
    module_id: int
    puede_ver: bool = False
    puede_crear: bool = False
    puede_editar: bool = False
    puede_eliminar: bool = False
    alcance: PermissionScope = PermissionScope.ALL


class RoleModuleResponse(BaseModel):
    id: int
    role_id: int
    role_name: str
    module_id: int
    module_name: str
    puede_ver: bool
    puede_crear: bool
    puede_editar: bool
    puede_eliminar: bool
    alcance: PermissionScope
    estado: bool


class MyPermissionResponse(BaseModel):
    """Módulos y permisos del usuario autenticado (para armar el menú del frontend)."""
    modulo: str
    ruta: str
    puede_ver: bool
    puede_crear: bool
    puede_editar: bool
    puede_eliminar: bool
    alcance: PermissionScope


# ===== PIAR =====

class CreateSpecialNeedRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class SpecialNeedResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    estado: bool

    class Config:
        from_attributes = True


class PiarNeedInput(BaseModel):
    special_need_id: int
    diagnostico: Optional[str] = None


class CreatePiarRequest(BaseModel):
    student_id: int
    school_year: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    observaciones: Optional[str] = None
    consentimiento_acudiente: bool = False
    needs: List[PiarNeedInput] = []


class UpdatePiarRequest(BaseModel):
    fecha_fin: Optional[date] = None
    observaciones: Optional[str] = None
    consentimiento_acudiente: bool


class CreatePiarGoalRequest(BaseModel):
    piar_id: int
    course_subject_id: Optional[int] = None
    descripcion: str


class CreatePiarAdjustmentRequest(BaseModel):
    piar_id: int
    course_subject_id: Optional[int] = None
    tipo: AdjustmentType
    descripcion: str


class CreatePiarProgressRequest(BaseModel):
    piar_goal_id: int
    period: Period
    nivel: ProgressLevel
    observaciones: Optional[str] = None


class PiarNeedResponse(BaseModel):
    special_need_id: int
    nombre: str
    diagnostico: Optional[str]


class PiarGoalResponse(BaseModel):
    id: int
    piar_id: int
    course_subject_id: Optional[int]
    subject_name: Optional[str]
    descripcion: str


class PiarAdjustmentResponse(BaseModel):
    id: int
    piar_id: int
    course_subject_id: Optional[int]
    subject_name: Optional[str]
    tipo: AdjustmentType
    descripcion: str


class PiarProgressResponse(BaseModel):
    id: int
    piar_goal_id: int
    period: Period
    nivel: ProgressLevel
    observaciones: Optional[str]
    registrado_por: int
    teacher_name: str


class PiarResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    school_year: int
    fecha_inicio: date
    fecha_fin: Optional[date]
    observaciones: Optional[str]
    consentimiento_acudiente: bool
    needs: List[PiarNeedResponse] = []
    goals: List[PiarGoalResponse] = []
    adjustments: List[PiarAdjustmentResponse] = []
    estado: bool


class UpdateRoleModuleRequest(BaseModel):
    puede_ver: bool = False
    puede_crear: bool = False
    puede_editar: bool = False
    puede_eliminar: bool = False
    alcance: PermissionScope = PermissionScope.ALL


class UpdatePiarProgressRequest(BaseModel):
    nivel: ProgressLevel
    observaciones: Optional[str] = None
