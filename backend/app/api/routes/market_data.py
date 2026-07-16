from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, UploadFile

from backend.app.core.exceptions import AppError
from backend.app.models.schemas import Category, MarketDataImportResponse, MarketDataListResponse, MarketSampleSourceType
from backend.app.repositories.product_repository import ProductRepository
from backend.app.services.market_data_import_service import MarketDataImportService


router = APIRouter()
repo = ProductRepository()


@router.get("/samples", response_model=MarketDataListResponse)
def list_market_data_samples(
    category: Category | None = Query(default=None),
    source_type: MarketSampleSourceType | None = Query(default=None),
    source_name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> MarketDataListResponse:
    return MarketDataListResponse(
        **repo.list_reference_items(
            category=category,
            source_type=source_type,
            source_name=source_name,
            limit=limit,
        )
    )


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


@router.delete("/samples/{item_id}", status_code=204)
def delete_market_data_sample(item_id: int) -> None:
    repo.delete_reference_item(item_id)
