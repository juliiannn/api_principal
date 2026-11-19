"""IA en la nube para el Asistente IA (proxy hacia Groq; la clave nunca llega al navegador)."""
from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from app.config.access import Access
from app.config.jwt_authentication import require_permission
from app.dto.request.assistant import AssistantChatRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.assistant import AssistantChatResponse, AssistantStatusResponse
from app.service import cloud_ai_service

MODULE = "Asistente IA"
router = APIRouter(prefix="/assistant", tags=["Asistente IA"])


@router.get("/status", response_model=ApiResponse[AssistantStatusResponse])
def status(access: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Assistant status", data=cloud_ai_service.status())


@router.post("/chat", response_model=ApiResponse[AssistantChatResponse])
async def chat(request: AssistantChatRequest, access: Access = Depends(require_permission(MODULE, "ver"))):
    data = await run_in_threadpool(cloud_ai_service.chat, access.user.id, request.messages)
    return ApiResponse(success=True, message="Answer generated", data=data)
