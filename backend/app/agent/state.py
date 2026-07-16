from __future__ import annotations

from typing import Any, Literal, TypedDict


class SaleAgentState(TypedDict, total=False):
    session_id: str
    current_step: str

    image_paths: list[str]
    image_original_names: list[str]
    category: Literal["digital", "book", "appliance", "clothing", "furniture", "shoe_bag"]
    product_type: str
    brand: str | None
    model: str | None
    color: str | None
    visible_condition: str | None
    visible_defects: list[str]
    vision_confidence: float

    original_price: float | None
    purchase_date: str | None
    functional_status: str | None
    repair_history: str | None
    accessories: list[str]
    additional_defects: list[str]
    size: str | None
    material: str | None
    wear_status: str | None
    wash_status: str | None
    dimensions: str | None
    installation_status: str | None
    pickup_requirement: str | None
    clean_status: str | None
    authenticity_status: str | None
    user_answers: dict[str, Any]
    confirmed: bool

    missing_fields: list[str]
    current_question: str | None

    similar_items: list[dict[str, Any]]
    image_similarity_summary: dict[str, Any]
    listing_price: float | None
    deal_price_min: float | None
    deal_price_max: float | None
    suggested_floor_price: float | None
    user_floor_price: float | None
    price_confidence: str | None
    price_reasons: list[str]
    price_breakdown: dict[str, Any]

    title: str | None
    description: str | None
    keywords: list[str]
    defect_statement: str | None
    photo_suggestions: list[str]
    platform_copies: list[dict[str, Any]]
    sale_outcome: dict[str, Any] | None

    buyer_message: str | None
    buyer_intent: str | None
    suggested_reply: str | None

    errors: list[str]
    trace: list[dict[str, Any]]
