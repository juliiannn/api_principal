import enum
from datetime import date

from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Time, Numeric,
    Enum as SqlEnum, ForeignKey, UniqueConstraint, Text, Index, func, text
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    """Nombres de los roles (constantes). La fuente de verdad es la tabla roles."""
    ADMIN = "ADMIN"
    RECTOR = "RECTOR"
    COORDINATOR = "COORDINATOR"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class DocumentType(str, enum.Enum):
    TI = "TI"
    CC = "CC"
    CE = "CE"
    PASSPORT = "PASSPORT"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class EducationLevel(str, enum.Enum):
    BACHELOR = "BACHELOR"
    UNDERGRADUATE = "UNDERGRADUATE"
    SPECIALIST = "SPECIALIST"
    MASTER = "MASTER"
    DOCTORATE = "DOCTORATE"


class ContractType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    HOURLY = "HOURLY"
    TEMPORARY = "TEMPORARY"


class CoordinationArea(str, enum.Enum):
    ACADEMIC = "ACADEMIC"
    DISCIPLINE = "DISCIPLINE"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class Period(str, enum.Enum):
    PERIOD_1 = "PERIOD_1"
    PERIOD_2 = "PERIOD_2"
    PERIOD_3 = "PERIOD_3"
    PERIOD_4 = "PERIOD_4"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"


class DayOfWeek(str, enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"


class PermissionScope(str, enum.Enum):
    ALL = "ALL"
    ASSIGNED = "ASSIGNED"
    OWN = "OWN"


class AdjustmentType(str, enum.Enum):
    ACCESS = "ACCESS"
    CURRICULAR = "CURRICULAR"
    METHODOLOGICAL = "METHODOLOGICAL"
    EVALUATIVE = "EVALUATIVE"


class ProgressLevel(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ACHIEVED = "ACHIEVED"


class AuditMixin:
    """Campos de control en TODAS las tablas.
    estado: True = activo, False = eliminado (borrado lógico).
    creado / actualizado: los gestiona la base de datos (default NOW() y trigger).
    """
    estado = Column(Boolean, nullable=False, default=True, server_default=text("TRUE"))
    creado = Column(DateTime, nullable=False, server_default=func.now())
    actualizado = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Role(AuditMixin, Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)

    users = relationship("User", back_populates="role_ref")
    permissions = relationship("RoleModule", back_populates="role")


class Module(AuditMixin, Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    ruta = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)

    permissions = relationship("RoleModule", back_populates="module")


class RoleModule(AuditMixin, Base):
    __tablename__ = "role_modules"
    __table_args__ = (UniqueConstraint("role_id", "module_id"),)

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    puede_ver = Column(Boolean, nullable=False, default=False)
    puede_crear = Column(Boolean, nullable=False, default=False)
    puede_editar = Column(Boolean, nullable=False, default=False)
    puede_eliminar = Column(Boolean, nullable=False, default=False)
    alcance = Column(SqlEnum(PermissionScope), nullable=False, default=PermissionScope.ALL)

    role = relationship("Role", back_populates="permissions")
    module = relationship("Module", back_populates="permissions")


class User(AuditMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(SqlEnum(DocumentType), nullable=False)
    document = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(SqlEnum(Gender), nullable=False)
    address = Column(String, nullable=False)
    password = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)

    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    coordinator_profile = relationship("Coordinator", back_populates="user", uselist=False)
    rector_profile = relationship("Rector", back_populates="user", uselist=False)
    role_ref = relationship("Role", back_populates="users", lazy="joined")

    @property
    def role(self) -> UserRole:
        """Compatibilidad: current_user.role.value sigue funcionando. Es de solo lectura;
        para asignar un rol usa role_id."""
        return UserRole(self.role_ref.nombre)


class Student(AuditMixin, Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    guardian_name = Column(String, nullable=False)
    guardian_phone = Column(String, nullable=False)
    guardian_email = Column(String, nullable=False)

    user = relationship("User", back_populates="student_profile")
    enrollments = relationship("Enrollment", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    piars = relationship("Piar", back_populates="student")


class Teacher(AuditMixin, Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    employee_code = Column(String, unique=True, nullable=False)
    hire_date = Column(Date, nullable=False)
    profession = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    education_level = Column(SqlEnum(EducationLevel), nullable=False)
    contract_type = Column(SqlEnum(ContractType), nullable=False)

    user = relationship("User", back_populates="teacher_profile")
    course_subjects = relationship("CourseSubject", back_populates="teacher")
    directed_courses = relationship("Course", back_populates="director_teacher")


class Coordinator(AuditMixin, Base):
    __tablename__ = "coordinators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    employee_code = Column(String, unique=True, nullable=False)
    area = Column(SqlEnum(CoordinationArea), nullable=False)
    assignment_date = Column(Date, nullable=False)
    education_level = Column(SqlEnum(EducationLevel), nullable=False)

    user = relationship("User", back_populates="coordinator_profile")


class Rector(AuditMixin, Base):
    __tablename__ = "rectors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    employee_code = Column(String, unique=True, nullable=False)
    appointment_date = Column(Date, nullable=False)
    administrative_period = Column(String, nullable=False)
    education_level = Column(SqlEnum(EducationLevel), nullable=False)

    user = relationship("User", back_populates="rector_profile")


class Course(AuditMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (Index("uq_courses_name_classroom_year", "name", "classroom", "school_year",
                            unique=True, postgresql_where=text("estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    classroom = Column(String, nullable=False)
    school_year = Column(Integer, nullable=False)
    director_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    director_teacher = relationship("Teacher", back_populates="directed_courses")
    enrollments = relationship("Enrollment", back_populates="course")
    course_subjects = relationship("CourseSubject", back_populates="course")


class Subject(AuditMixin, Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    course_subjects = relationship("CourseSubject", back_populates="subject")


class CourseSubject(AuditMixin, Base):
    __tablename__ = "course_subjects"
    __table_args__ = (Index("uq_course_subjects_course_subject", "course_id", "subject_id",
                            unique=True, postgresql_where=text("estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    course = relationship("Course", back_populates="course_subjects")
    subject = relationship("Subject", back_populates="course_subjects")
    teacher = relationship("Teacher", back_populates="course_subjects")
    grades = relationship("Grade", back_populates="course_subject")
    attendances = relationship("Attendance", back_populates="course_subject")
    schedules = relationship("Schedule", back_populates="course_subject")
    assignments = relationship("Assignment", back_populates="course_subject")


class Enrollment(AuditMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (Index("uq_enrollments_student_course_active", "student_id", "course_id",
                            unique=True, postgresql_where=text("status = 'ACTIVE' AND estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(Date, nullable=False, default=date.today)
    status = Column(SqlEnum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.ACTIVE)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class Grade(AuditMixin, Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("student_id", "course_subject_id", "period"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    period = Column(SqlEnum(Period), nullable=False)
    value = Column(Numeric(3, 1), nullable=False)

    student = relationship("Student", back_populates="grades")
    course_subject = relationship("CourseSubject", back_populates="grades")


class Attendance(AuditMixin, Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("student_id", "course_subject_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(SqlEnum(AttendanceStatus), nullable=False)

    student = relationship("Student", back_populates="attendances")
    course_subject = relationship("CourseSubject", back_populates="attendances")


class Schedule(AuditMixin, Base):
    __tablename__ = "schedules"
    __table_args__ = (Index("uq_schedules_slot", "course_subject_id", "day_of_week", "start_time",
                            unique=True, postgresql_where=text("estado = TRUE")),)

    id = Column(Integer, primary_key=True, index=True)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    day_of_week = Column(SqlEnum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    course_subject = relationship("CourseSubject", back_populates="schedules")


class Assignment(AuditMixin, Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)

    course_subject = relationship("CourseSubject", back_populates="assignments")


# ===== PIAR: Plan Individual de Ajustes Razonables (Decreto 1421 de 2017) =====

class SpecialNeed(AuditMixin, Base):
    __tablename__ = "special_needs"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)

    piar_needs = relationship("PiarNeed", back_populates="special_need")


class Piar(AuditMixin, Base):
    __tablename__ = "piars"
    __table_args__ = (UniqueConstraint("student_id", "school_year"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    school_year = Column(Integer, nullable=False)
    fecha_inicio = Column(Date, nullable=False, default=date.today)
    fecha_fin = Column(Date, nullable=True)
    observaciones = Column(Text, nullable=True)
    consentimiento_acudiente = Column(Boolean, nullable=False, default=False)
    elaborado_por = Column(Integer, ForeignKey("users.id"), nullable=False)

    student = relationship("Student", back_populates="piars")
    author = relationship("User")
    needs = relationship("PiarNeed", back_populates="piar")
    goals = relationship("PiarGoal", back_populates="piar")
    adjustments = relationship("PiarAdjustment", back_populates="piar")


class PiarNeed(AuditMixin, Base):
    __tablename__ = "piar_needs"
    __table_args__ = (UniqueConstraint("piar_id", "special_need_id"),)

    id = Column(Integer, primary_key=True, index=True)
    piar_id = Column(Integer, ForeignKey("piars.id"), nullable=False)
    special_need_id = Column(Integer, ForeignKey("special_needs.id"), nullable=False)
    diagnostico = Column(Text, nullable=True)

    piar = relationship("Piar", back_populates="needs")
    special_need = relationship("SpecialNeed", back_populates="piar_needs")


class PiarGoal(AuditMixin, Base):
    __tablename__ = "piar_goals"

    id = Column(Integer, primary_key=True, index=True)
    piar_id = Column(Integer, ForeignKey("piars.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=True)
    descripcion = Column(Text, nullable=False)

    piar = relationship("Piar", back_populates="goals")
    course_subject = relationship("CourseSubject")
    progress = relationship("PiarProgress", back_populates="goal")


class PiarAdjustment(AuditMixin, Base):
    __tablename__ = "piar_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    piar_id = Column(Integer, ForeignKey("piars.id"), nullable=False)
    course_subject_id = Column(Integer, ForeignKey("course_subjects.id"), nullable=True)
    tipo = Column(SqlEnum(AdjustmentType), nullable=False)
    descripcion = Column(Text, nullable=False)

    piar = relationship("Piar", back_populates="adjustments")
    course_subject = relationship("CourseSubject")


class PiarProgress(AuditMixin, Base):
    __tablename__ = "piar_progress"
    __table_args__ = (UniqueConstraint("piar_goal_id", "period"),)

    id = Column(Integer, primary_key=True, index=True)
    piar_goal_id = Column(Integer, ForeignKey("piar_goals.id"), nullable=False)
    period = Column(SqlEnum(Period), nullable=False)
    nivel = Column(SqlEnum(ProgressLevel), nullable=False, default=ProgressLevel.NOT_STARTED)
    observaciones = Column(Text, nullable=True)
    registrado_por = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    goal = relationship("PiarGoal", back_populates="progress")
    teacher = relationship("Teacher")
