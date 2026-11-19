"""IA en la nube con Groq (API compatible con OpenAI: POST /chat/completions).

- La clave (GROQ_API_KEY) vive SOLO en el servidor (.env / Render). El navegador nunca la ve.
- El frontend envía la conversación ya armada y sin nombres reales (códigos EST-12 / DOC-3).
- Límite propio por usuario (AI_MAX_REQUESTS_PER_MINUTE) para no agotar el plan gratuito de Groq.
"""
import json
import re
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from typing import Deque, Dict, List

from app.config.settings import settings
from app.dto.request.assistant import AssistantTurn
from app.dto.response.assistant import AssistantChatResponse, AssistantStatusResponse
from app.exception import ApiException, InvalidRequestException

PROVIDER = "groq"


class CloudAiUnavailable(ApiException):
    """503: la IA en la nube no está configurada o no respondió."""

    def __init__(self, message: str):
        super().__init__(message, 503)


class CloudAiRateLimited(ApiException):
    def __init__(self, message: str):
        super().__init__(message, 429)


_calls: Dict[int, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def status() -> AssistantStatusResponse:
    return AssistantStatusResponse(configured=bool(settings.GROQ_API_KEY), provider=PROVIDER,
                                   model=settings.GROQ_MODEL if settings.GROQ_API_KEY else None)


def _check_rate(user_id: int) -> None:
    now = time.monotonic()
    with _lock:
        window = _calls[user_id]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.AI_MAX_REQUESTS_PER_MINUTE:
            raise CloudAiRateLimited("Too many AI questions; wait a minute")
        window.append(now)


def _clean(text: str) -> str:
    """Quita cualquier razonamiento que se cuele (<think>…</think>)."""
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.I)   # bloques completos
    closing = text.lower().rfind("</think>")                          # cierre suelto: el bloque empezó en la plantilla
    if closing >= 0:
        text = text[closing + len("</think>"):]
    return text.strip()


def chat(user_id: int, messages: List[AssistantTurn]) -> AssistantChatResponse:
    if not settings.GROQ_API_KEY:
        raise CloudAiUnavailable("Cloud AI is not configured (GROQ_API_KEY)")
    _check_rate(user_id)

    model = settings.GROQ_MODEL
    payload: dict = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": 0.5,
        "max_completion_tokens": 2048,
    }
    if model.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"     # piensa poco: responde más rápido y gasta menos cupo

    request = urllib.request.Request(
        settings.GROQ_API_URL, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "sistema-academico-piar/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.AI_TIMEOUT,
                                    context=ssl.create_default_context()) as response:
            body = json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read() or b"{}").get("error", {})
        except ValueError:
            detail = {}
        message = str(detail.get("message", "")) if isinstance(detail, dict) else ""
        code = str(detail.get("code", "")) if isinstance(detail, dict) else ""
        if e.code == 401:
            raise CloudAiUnavailable("The Groq API key is invalid") from None
        if e.code == 429:
            raise CloudAiRateLimited("The free AI quota is exhausted for now; wait a minute") from None
        if e.code in (400, 404) and ("decommission" in message.lower() or "model" in code or "does not exist" in message.lower()):
            raise CloudAiUnavailable(f"The AI model {model} is not available in Groq; change GROQ_MODEL") from None
        if e.code == 413 or "too large" in message.lower():
            raise InvalidRequestException("The question carries too much data for the AI; ask something more specific") from None
        raise CloudAiUnavailable(f"Groq answered with error {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise CloudAiUnavailable("Could not reach the cloud AI") from None

    try:
        choice = body["choices"][0]["message"]
        content = _clean(str(choice.get("content") or ""))
    except (KeyError, IndexError, TypeError):
        content = ""
    if not content:
        raise CloudAiUnavailable("The cloud AI returned an empty answer")
    usage = body.get("usage") or {}
    return AssistantChatResponse(content=content, model=str(body.get("model") or model), provider=PROVIDER,
                                 total_tokens=usage.get("total_tokens"))
