from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


Category = Literal["digital", "book", "appliance"]


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

    # 三类商品共用的补充字段，未知字段会保存在 user_answers。
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
