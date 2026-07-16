from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from backend.app.core.exceptions import AppError
from backend.app.models.schemas import MarketDataImportResponse
from backend.app.services.market_data_import_service import MarketDataImportService


router = APIRouter()


@router.post("/import", response_model=MarketDataImportResponse)
async def import_market_data(
    file: UploadFile = File(...),
    source_name: str | None = Form(default=None),
) -> MarketDataImportResponse:
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise AppError("价格样本仅支持 CSV 文件")

    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise AppError("CSV 文件不能超过 2 MB")

    result = MarketDataImportService().import_csv(content, source_name)
    return MarketDataImportResponse(**result)
