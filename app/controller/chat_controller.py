"""Chat en tiempo real.

WebSocket  /ws/chat   (protocolo JSON, ver docstring de chat_socket)
REST       /chat/...  (historial, conversaciones, contactos, abrir chat privado, marcar leído)
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.config.access import Access
from app.config.database import SessionLocal, get_db
from app.config.jwt_authentication import require_permission
from app.dto.request.chat import ChatDirectRequest, ChatReadRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.chat import ChatConversationResponse, ChatMessageResponse, ChatUserResponse
from app.exception import ApiException
from app.model import ChatConversationType, User
from app.repository.role_module_repository import RoleModuleRepository
from app.service.chat_service import ChatService
from app.service.jwt_service import JwtService
from app.websocket.chat_manager import manager

MODULE = "Chat"
AUTH_TIMEOUT_SECONDS = 10
IDLE_TIMEOUT_SECONDS = 75     # el cliente envía "ping" cada 25 s; si no llega nada en 75 s se cierra

log = logging.getLogger("chat")
router = APIRouter(tags=["Chat"])


# =====================================================================================
# REST
# =====================================================================================

@router.get("/chat/conversations", response_model=ApiResponse[List[ChatConversationResponse]])
def conversations(db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "ver"))):
    data = ChatService(db).conversations(access.user, manager.online_ids())
    return ApiResponse(success=True, message="Conversations retrieved", data=data)


@router.get("/chat/conversations/{conversation_id}/messages", response_model=ApiResponse[List[ChatMessageResponse]])
def messages(conversation_id: int, before: Optional[int] = Query(None, gt=0), limit: int = Query(50, ge=1, le=100),
             db: Session = Depends(get_db), access: Access = Depends(require_permission(MODULE, "ver"))):
    data = ChatService(db).history(access.user, conversation_id, before, limit, manager.online_ids())
    return ApiResponse(success=True, message="Messages retrieved", data=data)


@router.get("/chat/contacts", response_model=ApiResponse[List[ChatUserResponse]])
def contacts(q: str = Query("", max_length=80), db: Session = Depends(get_db),
             access: Access = Depends(require_permission(MODULE, "ver"))):
    data = ChatService(db).contacts(access.user, manager.online_ids(), q)
    return ApiResponse(success=True, message="Contacts retrieved", data=data)


@router.post("/chat/direct", response_model=ApiResponse[ChatConversationResponse])
def open_direct(request: ChatDirectRequest, db: Session = Depends(get_db),
                access: Access = Depends(require_permission(MODULE, "crear"))):
    data = ChatService(db).open_direct(access.user, request.user_id, manager.online_ids())
    return ApiResponse(success=True, message="Conversation ready", data=data)


@router.post("/chat/conversations/{conversation_id}/read", response_model=ApiResponse[int])
def mark_read(conversation_id: int, request: ChatReadRequest, db: Session = Depends(get_db),
              access: Access = Depends(require_permission(MODULE, "ver"))):
    _, last_read = ChatService(db).mark_read(access.user, conversation_id, request.message_id)
    return ApiResponse(success=True, message="Marked as read", data=last_read)


@router.get("/chat/online", response_model=ApiResponse[List[int]])
def online(access: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Online users", data=sorted(manager.online_ids()))


# =====================================================================================
# WebSocket
# =====================================================================================

def _dump(model) -> Dict[str, Any]:
    return model.model_dump(by_alias=True, mode="json")


def _authenticate(token: Any) -> Optional[Dict[str, Any]]:
    """Valida el JWT y el permiso «ver» del módulo Chat. Devuelve los datos públicos del usuario."""
    if not isinstance(token, str) or not token:
        return None
    payload = JwtService().decode_access_token(token)
    if payload is None:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == payload.get("sub"), User.estado.is_(True)).first()
        if user is None or not user.enabled or not user.role_ref.estado:
            return None
        perm = RoleModuleRepository(db).find_permission(user.role_id, MODULE)
        if perm is None or not perm.puede_ver:
            return {"forbidden": True}
        return {"id": user.id, "can_write": bool(perm.puede_crear),
                "user": _dump(ChatService.user_dto(user, manager.online_ids() | {user.id}))}
    finally:
        db.close()


def _send_message(user_id: int, conversation_id: Any, content: Any) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        service = ChatService(db)
        user = service.find_user(user_id)
        message, conv = service.send(user, int(conversation_id), content)
        return {"message": _dump(service.message_dto(message, manager.online_ids())),
                "recipients": service.recipients(conv), "type": conv.tipo}
    finally:
        db.close()


def _conversation_recipients(user_id: int, conversation_id: Any) -> Optional[set]:
    db = SessionLocal()
    try:
        service = ChatService(db)
        conv = service.get_conversation_for(service.find_user(user_id), int(conversation_id))
        return service.recipients(conv)
    finally:
        db.close()


def _mark_read(user_id: int, conversation_id: Any, message_id: Any) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        service = ChatService(db)
        conv, last_read = service.mark_read(service.find_user(user_id), int(conversation_id), int(message_id))
        return {"recipients": service.recipients(conv), "last_read": last_read, "type": conv.tipo}
    finally:
        db.close()


async def _error(ws: WebSocket, code: str, message: str, client_id: Any = None) -> None:
    payload: Dict[str, Any] = {"type": "error", "code": code, "message": message}
    if client_id is not None:
        payload["clientId"] = client_id
    await manager._safe_send(ws, payload)


@router.websocket("/ws/chat")
async def chat_socket(ws: WebSocket):
    """Protocolo (JSON):
    cliente -> servidor
      {"type":"auth","token":"<JWT>"}                     primer mensaje obligatorio (el token NO va en la URL)
      {"type":"message","conversationId":1,"content":"Hola","clientId":"abc"}
      {"type":"typing","conversationId":1}
      {"type":"read","conversationId":1,"messageId":15}
      {"type":"ping"}
    servidor -> cliente
      ready {user, onlineUserIds} · message {message, clientId} · presence {user, online, onlineUserIds}
      typing {conversationId, user} · read {conversationId, userId, messageId} · pong · error {code, message}
    Códigos de cierre: 4401 sin autenticar, 4403 sin permiso, 4408 inactivo.
    """
    await ws.accept()
    try:
        first = await asyncio.wait_for(ws.receive_json(), timeout=AUTH_TIMEOUT_SECONDS)
    except Exception:  # noqa: BLE001 - timeout, JSON inválido o desconexión
        await ws.close(code=4401)
        return
    auth = await run_in_threadpool(_authenticate, first.get("token") if isinstance(first, dict) and first.get("type") == "auth" else None)
    if auth is None:
        await _error(ws, "UNAUTHORIZED", "Sesión inválida o vencida. Vuelve a iniciar sesión.")
        await ws.close(code=4401)
        return
    if auth.get("forbidden"):
        await _error(ws, "FORBIDDEN", "Tu rol no tiene acceso al chat.")
        await ws.close(code=4403)
        return

    user_id: int = auth["id"]
    me: Dict[str, Any] = auth["user"]
    is_first = await manager.connect(user_id, ws)
    online_ids = sorted(manager.online_ids())
    await manager._safe_send(ws, {"type": "ready", "user": me, "onlineUserIds": online_ids})
    if is_first:
        await manager.send_to({"type": "presence", "user": {**me, "online": True}, "online": True,
                               "onlineUserIds": online_ids}, exclude=ws)
    log.info("Chat: conectado usuario %s (%s conexiones)", user_id, manager.connection_count())

    try:
        while True:
            try:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=IDLE_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                await ws.close(code=4408)
                break
            try:
                event = json.loads(raw)
                if not isinstance(event, dict):
                    raise ValueError
            except ValueError:
                await _error(ws, "BAD_JSON", "Mensaje con formato inválido.")
                continue

            kind = event.get("type")
            client_id = event.get("clientId")
            try:
                if kind == "ping":
                    await manager._safe_send(ws, {"type": "pong"})

                elif kind == "message":
                    if not auth["can_write"]:
                        await _error(ws, "FORBIDDEN", "Tu rol solo puede leer el chat.", client_id)
                    elif not manager.allow_message(user_id):
                        await _error(ws, "RATE_LIMIT", "Vas muy rápido. Espera unos segundos.", client_id)
                    else:
                        result = await run_in_threadpool(_send_message, user_id, event.get("conversationId"),
                                                         event.get("content"))
                        await manager.send_to({"type": "message", "message": result["message"], "clientId": client_id},
                                              result["recipients"])

                elif kind == "typing":
                    recipients = await run_in_threadpool(_conversation_recipients, user_id, event.get("conversationId"))
                    payload = {"type": "typing", "conversationId": event.get("conversationId"), "user": me}
                    others = None if recipients is None else recipients - {user_id}
                    if others is None:
                        await manager.send_to(payload, [u for u in manager.online_ids() if u != user_id])
                    elif others:
                        await manager.send_to(payload, others)

                elif kind == "read":
                    result = await run_in_threadpool(_mark_read, user_id, event.get("conversationId"),
                                                     event.get("messageId", 0))
                    if result["type"] == ChatConversationType.DIRECT.value:
                        await manager.send_to({"type": "read", "conversationId": event.get("conversationId"),
                                               "userId": user_id, "messageId": result["last_read"]},
                                              result["recipients"])
                else:
                    await _error(ws, "UNKNOWN_TYPE", "Tipo de mensaje desconocido.", client_id)

            except ApiException as e:
                await _error(ws, "INVALID", e.message, client_id)
            except (TypeError, ValueError):
                await _error(ws, "INVALID", "Datos incompletos en el mensaje.", client_id)
    except WebSocketDisconnect:
        pass
    except Exception as e:  # noqa: BLE001
        log.warning("Chat: error con el usuario %s: %s", user_id, e)
    finally:
        is_last = await manager.disconnect(user_id, ws)
        if is_last:
            await manager.send_to({"type": "presence", "user": {**me, "online": False}, "online": False,
                                   "onlineUserIds": sorted(manager.online_ids())})
        log.info("Chat: desconectado usuario %s", user_id)
