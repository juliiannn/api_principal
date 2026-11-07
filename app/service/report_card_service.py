from collections import defaultdict
from datetime import date as date_type
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from fastapi import Depends
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.exception import ResourceNotFoundException
from app.model import Period
from app.repository.grade_repository import GradeRepository
from app.repository.student_repository import StudentRepository

PERIOD_COLUMNS = {Period.PERIOD_1: 220, Period.PERIOD_2: 280, Period.PERIOD_3: 340, Period.PERIOD_4: 400}
_TWO_DECIMALS = Decimal("0.01")


class ReportCardService:
    """Genera el boletín de calificaciones de un estudiante en PDF."""

    def __init__(
        self,
        student_repository: StudentRepository = Depends(),
        grade_repository: GradeRepository = Depends(),
    ):
        self.student_repository = student_repository
        self.grade_repository = grade_repository

    def generate_pdf(self, student_id: int) -> bytes:
        student = self.student_repository.find_active_by_id(student_id)
        if student is None:
            raise ResourceNotFoundException(f"Student with id {student_id} not found")

        grades = self.grade_repository.find_active_by_student(student_id)

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
            subject_avg = (
                (sum(period_grades.values()) / Decimal(len(period_grades))).quantize(
                    _TWO_DECIMALS, rounding=ROUND_HALF_UP
                )
                if period_grades else Decimal("0")
            )
            c.setFont("Helvetica-Bold", 10)
            c.drawString(460, y, str(subject_avg))
            y -= 18

        y -= 10
        c.line(margin_left, y, 540, y)
        y -= 20

        overall_avg = (
            (overall_sum / Decimal(overall_count)).quantize(_TWO_DECIMALS, rounding=ROUND_HALF_UP)
            if overall_count > 0 else Decimal("0")
        )
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_left, y, f"Promedio general: {overall_avg}")

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()
