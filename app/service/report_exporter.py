"""Convierte un ReportData en Excel (XLSX, con openpyxl) o PDF (con reportlab)."""
from datetime import date, datetime
from html import escape
from io import BytesIO

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.service.report_builder import ReportData

SYSTEM = "Sistema Académico PIAR"
NAVY = "1E3A8A"
RED = "B91C1C"


def _cell_text(value, kind: str) -> str:
    if value is None:
        return "—"
    if kind == "decimal":
        return f"{value:.1f}"
    if kind == "percent":
        return f"{value * 100:.1f}%"
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    return str(value)


# ---------------------------------------------------------------- Excel

def to_xlsx(data: ReportData, generated_by: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"
    ncols = len(data.columns)
    last = get_column_letter(ncols)

    ws["A1"] = data.titulo
    ws["A1"].font = Font(size=15, bold=True, color=NAVY)
    ws["A2"] = data.filtros
    ws["A2"].font = Font(italic=True, color="475569")
    ws["A3"] = f"Generado el {datetime.now():%d/%m/%Y %H:%M} por {generated_by} · {SYSTEM}"
    ws["A3"].font = Font(size=9, color="64748B")
    for r in (1, 2, 3):
        ws.merge_cells(f"A{r}:{last}{r}")

    header_row = 5
    thin = Side(style="thin", color="CBD5E1")
    for i, col in enumerate(data.columns, start=1):
        c = ws.cell(row=header_row, column=i, value=col.header)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(bottom=thin, top=thin, left=thin, right=thin)
        ws.column_dimensions[get_column_letter(i)].width = max(col.width, len(col.header) + 2)
    ws.row_dimensions[header_row].height = 30

    formats = {"decimal": "0.0", "percent": "0.0%", "date": "DD/MM/YYYY", "number": "0"}
    for r, row in enumerate(data.rows, start=header_row + 1):
        for i, (value, col) in enumerate(zip(row, data.columns), start=1):
            c = ws.cell(row=r, column=i, value=value)
            c.border = Border(bottom=thin)
            if col.kind in formats:
                c.number_format = formats[col.kind]
            if col.kind in ("decimal", "percent", "number"):
                c.alignment = Alignment(horizontal="center")
            if r % 2 == 0:
                c.fill = PatternFill("solid", fgColor="F8FAFC")

    first, end = header_row + 1, header_row + max(len(data.rows), 1)
    for i, col in enumerate(data.columns, start=1):
        if col.alert_below is not None and data.rows:
            letter = get_column_letter(i)
            ws.conditional_formatting.add(
                f"{letter}{first}:{letter}{end}",
                CellIsRule(operator="lessThan", formula=[str(col.alert_below)],
                           font=Font(color=RED, bold=True), fill=PatternFill("solid", fgColor="FEE2E2")))
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)
    if data.rows:
        ws.auto_filter.ref = f"A{header_row}:{last}{end}"
    if data.truncated:
        ws.cell(row=end + 2, column=1, value="Reporte recortado: se alcanzó el máximo de filas permitido.").font = Font(color=RED)

    summary = wb.create_sheet("Resumen")
    summary["A1"] = f"Resumen · {data.titulo}"
    summary["A1"].font = Font(size=13, bold=True, color=NAVY)
    summary["A2"] = data.filtros
    summary["A2"].font = Font(italic=True, color="475569")
    for r, (label, value) in enumerate(data.summary, start=4):
        summary.cell(row=r, column=1, value=label).font = Font(bold=True)
        summary.cell(row=r, column=2, value=value)
    summary.column_dimensions["A"].width = 40
    summary.column_dimensions["B"].width = 18

    wb.properties.title = data.titulo
    wb.properties.creator = SYSTEM
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


# ---------------------------------------------------------------- PDF

def to_pdf(data: ReportData, generated_by: str) -> bytes:
    page = landscape(A4) if data.landscape else A4
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=page, leftMargin=12 * mm, rightMargin=12 * mm, topMargin=14 * mm,
                            bottomMargin=14 * mm, title=data.titulo, author=SYSTEM)
    title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=15, textColor=colors.HexColor(f"#{NAVY}"), spaceAfter=4)
    sub = ParagraphStyle("s", fontName="Helvetica-Oblique", fontSize=9, textColor=colors.HexColor("#475569"), spaceAfter=2)
    small = ParagraphStyle("m", fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor("#64748B"))
    cell = ParagraphStyle("c", fontName="Helvetica", fontSize=7.5, leading=9)
    head = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.white)

    story = [
        Paragraph(escape(data.titulo), title),
        Paragraph(escape(data.filtros), sub),
        Paragraph(f"Generado el {datetime.now():%d/%m/%Y %H:%M} por {escape(generated_by)}", small),
        Spacer(1, 6),
    ]

    # Indicadores del resumen en una fila de cajas
    if data.summary:
        kpi = ParagraphStyle("k", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#334155"))
        cells = [Paragraph(f"<font size=13><b>{escape(str(value))}</b></font><br/>{escape(label)}", kpi) for label, value in data.summary]
        kpis = Table([cells], colWidths=[(page[0] - 24 * mm) / len(cells)] * len(cells))
        kpis.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [kpis, Spacer(1, 8)]

    if not data.rows:
        story.append(Paragraph("No hay datos para los filtros elegidos.", sub))
    else:
        total_w = sum(c.width for c in data.columns)
        usable = page[0] - 24 * mm
        widths = [usable * c.width / total_w for c in data.columns]
        table_rows = [[Paragraph(escape(c.header), head) for c in data.columns]]
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{NAVY}")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for r, row in enumerate(data.rows, start=1):
            line = []
            for i, (value, col) in enumerate(zip(row, data.columns)):
                text = escape(_cell_text(value, col.kind))   # el texto del dato nunca se interpreta como marcado
                low = col.alert_below is not None and isinstance(value, (int, float)) and value < col.alert_below
                line.append(Paragraph(f"<font color='#{RED}'><b>{text}</b></font>" if low else text, cell))
                if col.kind in ("decimal", "percent", "number"):
                    style.append(("ALIGN", (i, r), (i, r), "CENTER"))
            table_rows.append(line)
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F8FAFC")))
        table = Table(table_rows, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle(style))
        story.append(table)
        if data.truncated:
            story.append(Paragraph("Reporte recortado: se alcanzó el máximo de filas permitido.", sub))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(12 * mm, 8 * mm, f"{SYSTEM} · {data.titulo}")
        canvas.drawRightString(page[0] - 12 * mm, 8 * mm, f"Página {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()
