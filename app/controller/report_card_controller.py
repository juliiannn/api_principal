from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.config.jwt_authentication import get_current_student, require_role
from app.model import Student, User
from app.service.report_card_service import ReportCardService

router = APIRouter(prefix="/report-cards", tags=["ReportCards"])


@router.get("/me")
def get_my_report_card(
    service: ReportCardService = Depends(), current_student: Student = Depends(get_current_student),
):
    pdf_bytes = service.generate_pdf(current_student.id)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=boletin.pdf"},
    )


@router.get("/{student_id}")
def get_report_card(
    student_id: int, service: ReportCardService = Depends(),
    _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR")),
):
    pdf_bytes = service.generate_pdf(student_id)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=boletin_{student_id}.pdf"},
    )
