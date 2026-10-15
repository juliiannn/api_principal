from dataclasses import dataclass
from typing import List, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Teacher, Student, Module, RoleModule, PermissionScope
from app.security import decode_access_token

bearer_scheme = HTTPBearer()

Action = Literal["ver", "crear", "editar", "eliminar"]
_ACTION_COLUMN = {
    "ver": "puede_ver",
    "crear": "puede_crear",
    "editar": "puede_editar",
    "eliminar": "puede_eliminar",
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    email = payload.get("sub")
    user = db.query(User).filter(User.email == email, User.estado.is_(True)).first()

    if user is None or not user.enabled or not user.role_ref.estado:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido o inactivo")

    return user


def require_role(*allowed_roles: str):
    """Se mantiene por compatibilidad con los routers actuales (compara por nombre de rol)."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_ref.nombre not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos suficientes")
        return current_user

    return role_checker


# ===== Permisos dinámicos (tabla role_modules) =====

@dataclass
class Access:
    """Resultado de una verificación de permiso: el usuario y el alcance con el que puede actuar."""
    user: User
    scope: PermissionScope


def _find_permission(db: Session, user: User, module_name: str):
    return (
        db.query(RoleModule)
        .join(Module, RoleModule.module_id == Module.id)
        .filter(
            RoleModule.role_id == user.role_id,
            RoleModule.estado.is_(True),
            Module.nombre == module_name,
            Module.estado.is_(True),
        )
        .first()
    )


def require_permission(module_name: str, action: Action):
    """Uso: access: Access = Depends(require_permission("Notas", "crear"))
    Luego access.scope indica ALL / ASSIGNED / OWN para filtrar los datos en el endpoint."""
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Access:
        perm = _find_permission(db, current_user, module_name)
        if perm is None or not getattr(perm, _ACTION_COLUMN[action]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos suficientes")
        return Access(user=current_user, scope=perm.alcance)

    return checker


def get_user_permissions(db: Session, user: User) -> List[RoleModule]:
    """Todos los permisos activos del rol del usuario (para el endpoint que arma el menú)."""
    return (
        db.query(RoleModule)
        .join(Module, RoleModule.module_id == Module.id)
        .filter(
            RoleModule.role_id == user.role_id,
            RoleModule.estado.is_(True),
            Module.estado.is_(True),
        )
        .all()
    )


# ===== Perfiles =====

def get_current_teacher(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Teacher:
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id, Teacher.estado.is_(True)).first()
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No teacher profile found")
    return teacher


def get_current_student(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Student:
    student = db.query(Student).filter(Student.user_id == current_user.id, Student.estado.is_(True)).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student profile found")
    return student
