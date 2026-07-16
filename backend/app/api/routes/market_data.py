from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, UploadFile

from backend.app.core.exceptions import AppError
from backend.app.models.schemas import (
    Category,
    MarketDataAuditResponse,
    MarketDataImportResponse,
    MarketDataListResponse,
    MarketDataSampleItem,
    MarketDataSampleUpdateRequest,
    MarketSampleAction,
    MarketSampleSourceType,
)
from backend.app.repositories.product_repository import ProductRepository
from backend.app.services.market_data_import_service import MarketDataImportService


router = APIRouter()
repo = ProductRepository()


@router.get("/audit", response_model=MarketDataAuditResponse)
def list_market_data_audit(
    item_id: int | None = Query(default=None),
    action: MarketSampleAction | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
) -> MarketDataAuditResponse:
    return MarketDataAuditResponse(**repo.list_sample_events(item_id=item_id, action=action, limit=limit))


@router.get("/samples", response_model=MarketDataListResponse)
def list_market_data_samples(
    category: Category | None = Query(default=None),
    source_type: MarketSampleSourceType | None = Query(default=None),
    source_name: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> MarketDataListResponse:
    return MarketDataListResponse(
        **repo.list_reference_items(
            category=category,
            source_type=source_type,
            source_name=source_name,
            active=active,
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


@router.patch("/samples/{item_id}", response_model=MarketDataSampleItem)
def update_market_data_sample(item_id: int, payload: MarketDataSampleUpdateRequest) -> MarketDataSampleItem:
    return MarketDataSampleItem(**repo.update_reference_item(item_id, payload.active, payload.user_notes))


@router.delete("/samples/{item_id}", status_code=204)
def delete_market_data_sample(item_id: int) -> None:
    repo.delete_reference_item(item_id)
