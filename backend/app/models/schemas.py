from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


Category = Literal["digital", "book", "appliance", "clothing", "furniture", "shoe_bag"]
InventoryStatus = Literal["draft", "ready", "listed", "sold", "archived"]
MarketSampleSourceType = Literal["seed", "imported"]
MarketSampleAction = Literal["import", "update", "disable", "restore", "delete"]


class SessionCreate(BaseModel):
    category: Category


class SaleStateResponse(BaseModel):
    session_id: str
    current_step: str
    state: dict[str, Any]


class SessionSummary(BaseModel):
    session_id: str
    category: Category
    current_step: str
    product_label: str
    inventory_status: InventoryStatus = "draft"
    created_at: str
    updated_at: str


class ProductConfirmation(BaseModel):
    category: Category
    product_type: str | None = None
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    visible_condition: str | None = None
    visible_defects: list[str] = Field(default_factory=list)
    vision_confidence: float | None = Field(default=None, ge=0, le=1)

    # 多类商品共用的补充字段，未知字段会保存在 user_answers。
    original_price: float | None = Field(default=None, ge=0)
    purchase_date: str | None = None
    functional_status: str | None = None
    repair_history: str | None = None
    accessories: list[str] = Field(default_factory=list)
    additional_defects: list[str] = Field(default_factory=list)
    delivery_options: str | None = None
    set_status: str | None = None
    notes_status: str | None = None
    damage_status: str | None = None
    size: str | None = None
    material: str | None = None
    wear_status: str | None = None
    wash_status: str | None = None
    dimensions: str | None = None
    installation_status: str | None = None
    pickup_requirement: str | None = None
    clean_status: str | None = None
    authenticity_status: str | None = None


class ConfirmRequest(BaseModel):
    product: ProductConfirmation


class NextQuestionResponse(BaseModel):
    completed: bool
    field: str | None = None
    question: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class AnswerRequest(BaseModel):
    field: str
    answer: Any


class SaleOutcomeRequest(BaseModel):
    final_sold_price: float = Field(ge=0)
    sold_channel: str | None = None
    sale_notes: str | None = None


class InventoryUpdateRequest(BaseModel):
    inventory_status: InventoryStatus
    storage_location: str | None = None
    inventory_notes: str | None = None


class ListingPerformanceRequest(BaseModel):
    days_listed: int = Field(ge=0)
    view_count: int = Field(ge=0)
    favorite_count: int = Field(ge=0)
    inquiry_count: int = Field(ge=0)
    current_listing_price: float | None = Field(default=None, ge=0)


class InventorySummaryItem(BaseModel):
    session_id: str
    category: Category
    category_label: str
    product_label: str
    inventory_status: InventoryStatus
    listing_price: float | None = None
    suggested_floor_price: float | None = None
    days_listed: int | None = None
    view_count: int | None = None
    favorite_count: int | None = None
    inquiry_count: int | None = None
    next_action: str | None = None
    updated_at: str


class InventorySummaryResponse(BaseModel):
    total_count: int
    by_status: dict[str, int]
    items: list[InventorySummaryItem]


class MarketDataImportError(BaseModel):
    row_number: int
    message: str


class MarketDataImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    error_count: int
    total_rows: int
    source_name: str
    accepted_columns: list[str]
    errors: list[MarketDataImportError] = Field(default_factory=list)


class MarketDataSampleUpdateRequest(BaseModel):
    active: bool | None = None
    user_notes: str | None = None


class MarketDataSampleItem(BaseModel):
    id: int
    category: Category
    category_label: str
    product_type: str
    brand: str | None = None
    model: str | None = None
    condition_level: str
    age_months: int
    original_price: float
    listing_price: float
    sold_price: float
    accessories_complete: bool
    description: str
    source_name: str
    source_type: MarketSampleSourceType
    source_url: str | None = None
    imported_at: str | None = None
    active: bool = True
    user_notes: str | None = None
    disabled_at: str | None = None
    deletable: bool = False
    editable: bool = False


class MarketDataListResponse(BaseModel):
    total_count: int
    by_source_type: dict[str, int]
    by_category: dict[str, int]
    by_active: dict[str, int]
    items: list[MarketDataSampleItem]


class MarketDataAuditItem(BaseModel):
    id: int
    item_id: int | None = None
    action: MarketSampleAction
    category: Category | None = None
    category_label: str | None = None
    product_type: str | None = None
    brand: str | None = None
    model: str | None = None
    source_name: str | None = None
    source_type: MarketSampleSourceType | None = None
    detail: dict[str, Any]
    created_at: str


class MarketDataAuditResponse(BaseModel):
    total_count: int
    items: list[MarketDataAuditItem]


class OutcomeSummaryItem(BaseModel):
    session_id: str
    category: Category
    product_label: str
    final_sold_price: float
    sold_channel: str
    price_position: str
    price_delta_from_mid: float | None = None
    price_delta_rate: float | None = None
    updated_at: str


class OutcomeCategorySummary(BaseModel):
    category: Category
    category_label: str
    total_count: int
    in_range_count: int
    in_range_rate: float
    average_delta_from_mid: float | None = None
    average_delta_rate: float | None = None
    total_sold_amount: float


class OutcomeSummaryResponse(BaseModel):
    total_count: int
    in_range_count: int
    in_range_rate: float
    average_delta_from_mid: float | None = None
    average_delta_rate: float | None = None
    total_sold_amount: float
    by_category: list[OutcomeCategorySummary]
    recent_outcomes: list[OutcomeSummaryItem]


class SimilarItem(BaseModel):
    id: int
    category: Category
    product_type: str
    brand: str | None = None
    model: str | None = None
    condition_level: str
    age_months: int
    original_price: float
    listing_price: float
    sold_price: float
    accessories_complete: bool
    description: str
    source_name: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    text_match_score: int | None = None
    image_similarity_score: int | None = None
    match_reasons: list[str] = Field(default_factory=list)


class PriceResult(BaseModel):
    listing_price: int
    deal_price_min: int
    deal_price_max: int
    suggested_floor_price: int
    price_confidence: Literal["低", "中", "高"]
    price_reasons: list[str]
    price_breakdown: dict[str, Any]


class PlatformCopy(BaseModel):
    platform: Literal["xianyu", "zhuanzhuan", "xiaohongshu"]
    platform_label: str
    title: str
    body: str
    tags: list[str]


class PublishChecklistItem(BaseModel):
    item_id: str
    title: str
    status: Literal["done", "review", "todo"]
    detail: str
    required: bool = True


class ListingResponse(BaseModel):
    session_id: str
    price: PriceResult
    similar_items: list[SimilarItem]
    title: str
    description: str
    keywords: list[str]
    defect_statement: str
    photo_suggestions: list[str]
    platform_copies: list[PlatformCopy]
    publish_checklist: list[PublishChecklistItem] = Field(default_factory=list)
    inventory_status: InventoryStatus = "ready"
    storage_location: str | None = None
    inventory_notes: str | None = None
    listing_performance: dict[str, Any] | None = None
    reprice_suggestion: dict[str, Any] | None = None
    sale_outcome: dict[str, Any] | None = None
    trace: list[dict[str, Any]]


class NegotiationRequest(BaseModel):
    buyer_message: str = Field(min_length=1)
    user_floor_price: float | None = Field(default=None, ge=0)


class NegotiationResponse(BaseModel):
    buyer_intent: str
    offer_price: float | None = None
    below_floor_price: bool
    suggested_reply: str
    next_strategy: str


class AnalyzeImageResponse(BaseModel):
    session_id: str
    image_paths: list[str]
    product: ProductConfirmation
    need_user_confirmation: bool = True


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app: str


class ExportResponse(BaseModel):
    markdown: str


class ErrorResponse(BaseModel):
    error: dict[str, str]


class UploadValidation:
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    allowed_content_types = {"image/jpeg", "image/png"}

    @staticmethod
    def normalize_suffix(filename: str) -> str:
        lowered = filename.lower()
        for suffix in UploadValidation.allowed_extensions:
            if lowered.endswith(suffix):
                return suffix
        return ""


class FieldAnswer(BaseModel):
    field: str
    answer: Any

    @field_validator("field")
    @classmethod
    def field_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field 不能为空")
        return value
