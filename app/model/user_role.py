import enum


class UserRole(str, enum.Enum):
    """Nombres de los roles (constantes). La fuente de verdad es la tabla roles."""
    ADMIN = "ADMIN"
    RECTOR = "RECTOR"
    COORDINATOR = "COORDINATOR"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
