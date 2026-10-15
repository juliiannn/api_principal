from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import date as date_type
from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_student, require_role
from app.exceptions import ResourceNotFoundException
from app.models import Grade, Period, Student, User

router = APIRouter(prefix="/report-cards", tags=["ReportCards"])

PERIOD_COLUMNS = {Period.PERIOD_1: 220, Period.PERIOD_2: 280, Period.PERIOD_3: 340, Period.PERIOD_4: 400}


def generate_pdf(db: Session, student_id: int) -> bytes:
    student = db.query(Student).filter(Student.id == student_id, Student.estado.is_(True)).first()
    if student is None:
        raise ResourceNotFoundException(f"Student with id {student_id} not found")

    grades = db.query(Grade).filter(Grade.student_id == student_id, Grade.estado.is_(True)).all()
    by_subject = defaultdict(dict)
    for g in grades:
        by_subject[g.course_subject.subject.name][g.period] = g.value

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    margin_left = 50
    y = 740

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_left, y, "Boletin de Calificaciones")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(margin_left, y, f"Estudiante: {student.user.full_name}")
    y -= 16
    c.drawString(margin_left, y, f"Documento: {student.user.document}")
    y -= 16
    c.drawString(margin_left, y, f"Fecha de generacion: {date_type.today().strftime('%d/%m/%Y')}")
    y -= 30

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left, y, "Materia")
    c.drawString(220, y, "P1")
    c.drawString(280, y, "P2")
    c.drawString(340, y, "P3")
    c.drawString(400, y, "P4")
    c.drawString(460, y, "Promedio")
    y -= 8
    c.line(margin_left, y, 540, y)
    y -= 14

    overall_sum = Decimal("0")
    overall_count = 0

    for subject_name, period_grades in by_subject.items():
        c.setFont("Helvetica", 10)
        c.drawString(margin_left, y, subject_name)

        for period, x in PERIOD_COLUMNS.items():
            value = period_grades.get(period)
            if value is not None:
                c.drawString(x, y, str(value))
                overall_sum += value
                overall_count += 1

        subject_avg = (sum(period_grades.values()) / Decimal(len(period_grades))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if period_grades else Decimal("0")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(460, y, str(subject_avg))
        y -= 18

    y -= 10
    c.line(margin_left, y, 540, y)
    y -= 20

    overall_avg = (overall_sum / Decimal(overall_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if overall_count > 0 else Decimal("0")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_left, y, f"Promedio general: {overall_avg}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


@router.get("/me")
def get_my_report_card(db: Session = Depends(get_db), current_student: Student = Depends(get_current_student)):
    pdf_bytes = generate_pdf(db, current_student.id)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=boletin.pdf"})


@router.get("/{student_id}")
def get_report_card(student_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "RECTOR", "COORDINATOR"))):
    pdf_bytes = generate_pdf(db, student_id)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=boletin_{student_id}.pdf"})
