"""Conexiones WebSocket abiertas del chat (en memoria del proceso).

- Un usuario puede tener varias pestañas: user_id -> conjunto de sockets. Está «en línea» mientras tenga al menos una.
- send_to(): reparte un evento a todos los conectados (sala general) o solo a ciertos usuarios (chat privado).
- Funciona con UN proceso de uvicorn (como en Render). Con varios procesos habría que unirlos con Redis pub/sub.
"""
import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Any, Deque, Dict, Iterable, Optional, Set

from fastapi import WebSocket

log = logging.getLogger("chat")

RATE_WINDOW_SECONDS = 5
RATE_MAX_MESSAGES = 8


class ChatConnectionManager:

    def __init__(self) -> None:
        self._sockets: Dict[int, Set[WebSocket]] = defaultdict(set)
        self._rate: Dict[int, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, ws: WebSocket) -> bool:
        """Registra el socket. True si es la PRIMERA conexión del usuario (acaba de entrar)."""
        async with self._lock:
            first = not self._sockets.get(user_id)
            self._sockets[user_id].add(ws)
            return first

    async def disconnect(self, user_id: int, ws: WebSocket) -> bool:
        """Quita el socket. True si era la ÚLTIMA conexión del usuario (salió del chat)."""
        async with self._lock:
            sockets = self._sockets.get(user_id)
            if not sockets:
                return False
            sockets.discard(ws)
            if sockets:
                return False
            self._sockets.pop(user_id, None)
            self._rate.pop(user_id, None)
            return True

    def online_ids(self) -> Set[int]:
        return {uid for uid, sockets in self._sockets.items() if sockets}

    def connection_count(self) -> int:
        return sum(len(s) for s in self._sockets.values())

    def allow_message(self, user_id: int) -> bool:
        """Límite anti-spam: máximo RATE_MAX_MESSAGES mensajes cada RATE_WINDOW_SECONDS segundos."""
        now = time.monotonic()
        window = self._rate[user_id]
        while window and now - window[0] > RATE_WINDOW_SECONDS:
            window.popleft()
        if len(window) >= RATE_MAX_MESSAGES:
            return False
        window.append(now)
        return True

    async def send_to(self, payload: Dict[str, Any], user_ids: Optional[Iterable[int]] = None,
                      exclude: Optional[WebSocket] = None) -> None:
        """user_ids=None -> todos los conectados."""
        targets = self.online_ids() if user_ids is None else set(user_ids)
        sockets = [ws for uid in targets for ws in list(self._sockets.get(uid, ())) if ws is not exclude]
        if sockets:
            await asyncio.gather(*(self._safe_send(ws, payload) for ws in sockets))

    @staticmethod
    async def _safe_send(ws: WebSocket, payload: Dict[str, Any]) -> None:
        try:
            await asyncio.wait_for(ws.send_json(payload), timeout=5)
        except Exception as e:  # noqa: BLE001 - un cliente caído no debe afectar a los demás
            log.debug("No se pudo enviar a un socket: %s", e)


manager = ChatConnectionManager()
