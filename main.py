from datetime import date, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.database import Base, engine, SessionLocal
from app.exceptions import ApiException
from app.models import User, Role, DocumentType, Gender
from app.security import hash_password
from app.routers import (
    auth, users, students, teachers, coordinators, rectors,
    courses, subjects, course_subjects, enrollments,
    grades, attendances, schedules, assignments,
    statistics, report_cards,
    roles, modules, role_modules, special_needs, piar,
)

app = FastAPI(title="Colegio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_error_body(status_code: int, error: str, message: str, path: str) -> dict:
    return {"timestamp": datetime.utcnow().isoformat(), "status": status_code, "error": error, "message": message, "path": path}


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    return JSONResponse(status_code=exc.status_code, content=build_error_body(exc.status_code, "Business Error", exc.message, request.url.path))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
    return JSONResponse(status_code=400, content=build_error_body(400, "Bad Request", messages, request.url.path))


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=build_error_body(500, "Internal Server Error", "Internal server error", request.url.path))


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(coordinators.router)
app.include_router(rectors.router)
app.include_router(courses.router)
app.include_router(subjects.router)
app.include_router(course_subjects.router)
app.include_router(enrollments.router)
app.include_router(grades.router)
app.include_router(attendances.router)
app.include_router(schedules.router)
app.include_router(assignments.router)
app.include_router(statistics.router)
app.include_router(report_cards.router)
app.include_router(roles.router)
app.include_router(modules.router)
app.include_router(role_modules.router)
app.include_router(special_needs.router)
app.include_router(piar.router)


@app.on_event("startup")
def on_startup():
    # La fuente de verdad del esquema es schema.sql (tipos, triggers e índices parciales).
    # create_all solo crea tablas que falten; no modifica las existentes.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.nombre == "ADMIN").first()
        if admin_role is None:
            raise RuntimeError("No existe el rol ADMIN. Ejecuta primero schema.sql (crea roles, módulos y permisos).")

        existing_admin = db.query(User).filter(User.email == "admin@colegio.com").first()
        if existing_admin is None:
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


@app.get("/")
def root():
    return {"message": "Colegio API - FastAPI"}
