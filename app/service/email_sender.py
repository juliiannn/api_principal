"""Envío de correo de forma segura, por SMTP o por la API HTTPS de Brevo (EMAIL_PROVIDER).

- La conexión va cifrada: STARTTLS (puerto 587) o SSL directo (465), verificando el certificado del servidor.
  Sin cifrado ("none") solo se acepta contra un servidor local (pruebas), para no mandar la contraseña en claro.
- Las credenciales salen de variables de entorno (.env); nunca se guardan en la base ni se escriben en el registro.
- Brevo (EMAIL_PROVIDER=brevo): el correo sale por HTTPS (puerto 443) con una API key. Se usa donde el hosting
  bloquea los puertos SMTP (Render gratis bloquea 25, 465 y 587).
- Modo prueba (EMAIL_REDIRECT_TO): todos los mensajes van a esa dirección; el destinatario real queda en el asunto.
"""
import base64
import json
import smtplib
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

from app.config.settings import settings

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass
class Attachment:
    """Archivo adjunto de un correo."""
    filename: str
    content: bytes
    mimetype: str   # p. ej. application/pdf


class EmailNotConfigured(Exception):
    """El servidor de correo no está configurado (falta SMTP_HOST o SMTP_FROM)."""


class EmailNotAllowed(EmailNotConfigured):
    """El destinatario no está en EMAIL_ALLOWED_DOMAINS: el correo queda OMITIDO (no se envía)."""


def is_allowed(address: str) -> bool:
    if not settings.EMAIL_ALLOWED_DOMAINS:
        return True
    domain = parseaddr(address)[1].rsplit("@", 1)[-1].lower()
    return domain in settings.EMAIL_ALLOWED_DOMAINS


def _is_brevo() -> bool:
    return settings.EMAIL_PROVIDER == "brevo"


def is_configured() -> bool:
    if _is_brevo():
        return bool(settings.BREVO_API_KEY and settings.SMTP_FROM)
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def is_valid_address(address: str) -> bool:
    _, email = parseaddr(address or "")
    return bool(email) and "@" in email and "." in email.split("@")[-1] and "\n" not in address


def config_status() -> dict:
    """Estado de la configuración, SIN secretos (para el panel del administrador)."""
    if _is_brevo():
        return {
            "configured": is_configured(), "host": "api.brevo.com", "port": 443, "security": "https (api brevo)",
            "sender": settings.SMTP_FROM or None, "redirect_to": settings.EMAIL_REDIRECT_TO or None,
            "allowed_domains": settings.EMAIL_ALLOWED_DOMAINS,
        }
    return {
        "configured": is_configured(),
        "host": settings.SMTP_HOST or None,
        "port": settings.SMTP_PORT if settings.SMTP_HOST else None,
        "security": settings.SMTP_SECURITY,
        "sender": settings.SMTP_FROM or None,
        "redirect_to": settings.EMAIL_REDIRECT_TO or None,
        "allowed_domains": settings.EMAIL_ALLOWED_DOMAINS,
    }


def send_email(to: str, subject: str, text: str, html: str, attachments: list[Attachment] | None = None) -> str:
    """Envía el correo y devuelve la dirección a la que salió de verdad. Lanza excepción si falla."""
    if not is_configured():
        raise EmailNotConfigured(
            "El correo no está configurado (BREVO_API_KEY / SMTP_FROM en el .env)." if _is_brevo()
            else "El correo no está configurado (SMTP_HOST / SMTP_FROM en el .env).")
    if not is_valid_address(to):
        raise ValueError(f"Dirección de correo no válida: {to!r}")

    real_to = to
    if settings.EMAIL_REDIRECT_TO:
        real_to = settings.EMAIL_REDIRECT_TO
        subject = f"[PRUEBA para {to}] {subject}"
    if not is_allowed(real_to):
        raise EmailNotAllowed(
            f"No se envió: el dominio de {real_to} no está en EMAIL_ALLOWED_DOMAINS "
            f"({', '.join(settings.EMAIL_ALLOWED_DOMAINS)}).")
    subject = subject.replace("\n", " ").replace("\r", " ").strip()[:250]

    if _is_brevo():
        _send_brevo(to, real_to, subject, text, html, attachments or [])
        return real_to

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = real_to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=(parseaddr(settings.SMTP_FROM)[1].split("@")[-1] or "localhost"))
    if real_to != to:
        msg["X-Original-To"] = to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    for a in attachments or []:
        maintype, subtype = a.mimetype.split("/", 1)
        msg.add_attachment(a.content, maintype=maintype, subtype=subtype, filename=a.filename)

    security = settings.SMTP_SECURITY
    context = ssl.create_default_context()   # verifica el certificado y el nombre del servidor
    if security == "ssl":
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT, context=context)
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT)
    try:
        if security == "starttls":
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        elif security == "none" and settings.SMTP_HOST not in LOCAL_HOSTS:
            raise RuntimeError("SMTP_SECURITY=none solo se permite con un servidor local; usa starttls o ssl.")
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass
    return real_to


def _send_brevo(original_to: str, real_to: str, subject: str, text: str, html: str,
                attachments: list[Attachment]) -> None:
    """POST https://api.brevo.com/v3/smtp/email (el remitente debe estar verificado en Brevo)."""
    name, sender = parseaddr(settings.SMTP_FROM)
    payload = {
        "sender": {"email": sender, **({"name": name} if name else {})},
        "to": [{"email": parseaddr(real_to)[1] or real_to}],
        "subject": subject,
        "textContent": text,
        "htmlContent": html,
    }
    if real_to != original_to:
        payload["headers"] = {"X-Original-To": original_to}
    if attachments:
        payload["attachment"] = [
            {"name": a.filename, "content": base64.b64encode(a.content).decode("ascii")} for a in attachments
        ]
    request = urllib.request.Request(
        settings.BREVO_API_URL, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.SMTP_TIMEOUT,
                                    context=ssl.create_default_context()) as response:
            if response.status >= 300:
                raise RuntimeError(f"Brevo respondió HTTP {response.status}")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read() or b"{}").get("message", "")
        except ValueError:
            detail = ""
        raise RuntimeError(f"Brevo rechazó el correo (HTTP {e.code}): {detail}".strip()) from None
