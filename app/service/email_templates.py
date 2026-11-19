"""Plantilla de los correos: versión HTML (con estilos en línea, como exigen los clientes de correo) y texto plano.
Todo el contenido variable se escapa, para que un dato (un nombre, una observación) no pueda inyectar HTML."""
from html import escape

from app.config.settings import settings

INSTITUTION = "Sistema Académico PIAR"


def render(title: str, body: str) -> tuple[str, str]:
    """body = párrafos separados por una línea en blanco. Devuelve (texto, html)."""
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    url = settings.FRONTEND_URL

    text = f"{title}\n\n" + "\n\n".join(paragraphs) + f"\n\nIngresa a la plataforma: {url}\n\n— {INSTITUTION}\n" \
           "Este es un mensaje automático; por favor no respondas a este correo."

    html_paragraphs = "".join(
        f'<p style="margin:0 0 14px;line-height:1.55;color:#334155;">{escape(p).replace(chr(10), "<br>")}</p>'
        for p in paragraphs
    )
    html = f"""<!DOCTYPE html>
<html lang="es"><body style="margin:0;padding:0;background:#f1f5f9;font-family:Segoe UI,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:24px 0;">
<tr><td align="center">
  <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">
    <tr><td style="background:#1e3a8a;padding:18px 24px;color:#ffffff;font-size:15px;font-weight:600;">{escape(INSTITUTION)}</td></tr>
    <tr><td style="padding:24px;">
      <h1 style="margin:0 0 16px;font-size:20px;color:#0f172a;">{escape(title)}</h1>
      {html_paragraphs}
      <p style="margin:22px 0 4px;"><a href="{escape(url)}" style="background:#2563eb;color:#ffffff;text-decoration:none;padding:10px 18px;border-radius:8px;font-weight:600;display:inline-block;">Abrir la plataforma</a></p>
    </td></tr>
    <tr><td style="padding:14px 24px;background:#f8fafc;color:#64748b;font-size:12px;">Mensaje automático de {escape(INSTITUTION)}. Por favor no respondas a este correo.</td></tr>
  </table>
</td></tr></table></body></html>"""
    return text, html
