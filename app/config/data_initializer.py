from datetime import date

from app.config.database import Base, SessionLocal, engine
from app.config.security_config import hash_password
from app.model import DocumentType, Gender, Role, User
from app.service.chat_service import ensure_general_room
from app.service.notification_service import ensure_default_settings


def initialize_data() -> None:
    """Crea las tablas que falten y el usuario administrador inicial (equivale a DataInitializer)."""
    # La fuente de verdad del esquema es schema.sql (tipos, triggers e índices parciales).
    # create_all solo crea tablas que falten; no modifica las existentes.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.nombre == "ADMIN").first()
        if admin_role is None:
            raise RuntimeError("No existe el rol ADMIN. Ejecuta primero schema.sql (crea roles, módulos y permisos).")

        ensure_default_settings(db)   # eventos de notificación por correo (activos o no)
        ensure_general_room(db)       # sala general del chat en tiempo real

        # Solo si NO hay ningún administrador (aunque le hayan cambiado el correo): así no se crea un segundo
        # admin con la contraseña por defecto cuando el admin original usa otro correo.
        existing_admin = db.query(User).filter(User.role_id == admin_role.id).first()
        if existing_admin is None and db.query(User).filter(User.email == "admin@colegio.com").first() is None:
            admin = User(
                document_type=DocumentType.CC, document="1000000000", email="admin@colegio.com",
                full_name="Administrador del Sistema", phone="3000000000", birth_date=date(1990, 1, 1),
                gender=Gender.MALE, address="Institucion Educativa", password=hash_password("Admin123."),
                must_change_password=False, role_id=admin_role.id,
            )
            db.add(admin)
            db.commit()
            print("=" * 42)
            print("Administrador creado correctamente")
            print("Correo: admin@colegio.com")
            print("Contraseña: Admin123.")
            print("=" * 42)
    finally:
        db.close()
