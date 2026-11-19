from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.config.access import Access
from app.config.jwt_authentication import require_permission
from app.dto.request.report import ReportEmailRequest, ReportRequest
from app.dto.response.api_response import ApiResponse
from app.dto.response.report import ReportCatalogItem, ReportEmailResponse, ReportFileResponse, ReportOptionsResponse
from app.service.report_service import MIME, ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

MODULE = "Reportes"


@router.get("/catalog", response_model=ApiResponse[List[ReportCatalogItem]])
def catalog(service: ReportService = Depends(), access: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Report catalog retrieved", data=service.catalog(access))


@router.get("/options", response_model=ApiResponse[ReportOptionsResponse])
def options(service: ReportService = Depends(), access: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Report options retrieved", data=service.options(access))


@router.get("/files", response_model=ApiResponse[List[ReportFileResponse]])
def my_files(service: ReportService = Depends(), access: Access = Depends(require_permission(MODULE, "ver"))):
    return ApiResponse(success=True, message="Report files retrieved", data=service.my_files(access))


@router.post("/generate", response_model=ApiResponse[ReportFileResponse])
def generate(request: ReportRequest, service: ReportService = Depends(),
             access: Access = Depends(require_permission(MODULE, "crear"))):
    return ApiResponse(success=True, message="Report generated successfully", data=service.generate(request, access))


@router.post("/email", response_model=ApiResponse[ReportEmailResponse])
def send_by_email(request: ReportEmailRequest, service: ReportService = Depends(),
                  access: Access = Depends(require_permission(MODULE, "crear"))):
    return ApiResponse(success=True, message="Report email processed", data=service.send_by_email(request, access))


@router.get("/files/{file_id}/download")
def download(file_id: int, service: ReportService = Depends(), access: Access = Depends(require_permission(MODULE, "ver"))):
    rf = service.file_for_download(file_id, access)
    return FileResponse(rf.ruta, media_type=MIME[rf.formato], filename=rf.nombre_archivo)
