from contextlib import asynccontextmanager

from fastapi.middleware.gzip import GZipMiddleware

from app.config.data_initializer import initialize_data
from app.config.openapi_config import create_app
from app.config.security_config import configure_cors
from app.controller import (
    assignment_controller, attendance_controller, auth_controller, coordinator_controller,
    course_controller, course_subject_controller, enrollment_controller, grade_controller,
    module_controller, piar_controller, rector_controller, report_card_controller,
    role_controller, role_module_controller, schedule_controller, special_need_controller,
    statistics_controller, student_controller, subject_controller, teacher_controller,
    user_controller, submission_controller, announcement_controller, notification_controller, report_controller, chat_controller,
    assistant_controller,
)
from app.exception.global_exception_handler import register_exception_handlers
from app.service.notification_service import resume_pending
from app.service.report_service import cleanup_expired_reports


@asynccontextmanager
async def lifespan(_):
    initialize_data()
    cleanup_expired_reports()   # borra los reportes temporales vencidos
    resume_pending()            # envía los correos que quedaron pendientes antes de reiniciar
    yield


app = create_app(lifespan)

configure_cors(app)
# Respuestas comprimidas: los listados grandes (notas, asistencia) pesan ~10 veces menos
app.add_middleware(GZipMiddleware, minimum_size=1000)
register_exception_handlers(app)

for controller in (
    auth_controller, user_controller, student_controller, teacher_controller, coordinator_controller,
    rector_controller, course_controller, subject_controller, course_subject_controller,
    enrollment_controller, grade_controller, attendance_controller, schedule_controller,
    assignment_controller, statistics_controller, report_card_controller, role_controller,
    module_controller, role_module_controller, special_need_controller, piar_controller,
    submission_controller, announcement_controller, notification_controller, report_controller, chat_controller,
    assistant_controller,
):
    app.include_router(controller.router)


@app.get("/")
def root():
    return {"message": "Colegio API - FastAPI"}
