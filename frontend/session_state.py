from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st


DEFAULTS = {
    "session_id": None,
    "category": "digital",
    "state": {},
    "analysis": None,
    "listing": None,
    "negotiation": None,
    "current_view": "开始出售",
}


PRODUCT_FIELDS = [
    "category",
    "product_type",
    "brand",
    "model",
    "color",
    "visible_condition",
    "visible_defects",
    "vision_confidence",
    "original_price",
    "purchase_date",
    "functional_status",
    "repair_history",
    "accessories",
    "additional_defects",
    "delivery_options",
    "set_status",
    "notes_status",
    "damage_status",
]


def init_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


def reset_flow() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = deepcopy(value)


def restore_flow(response: dict[str, Any]) -> None:
    state = response.get("state", {})
    reset_flow()
    st.session_state.session_id = response.get("session_id") or state.get("session_id")
    st.session_state.category = state.get("category", "digital")
    st.session_state.state = state
    st.session_state.analysis = _analysis_from_state(state)
    st.session_state.listing = _listing_from_state(state)
    st.session_state.negotiation = state.get("last_negotiation")
    st.session_state.current_view = _view_from_step(state.get("current_step"), bool(st.session_state.listing))


def _analysis_from_state(state: dict[str, Any]) -> dict[str, Any] | None:
    product = {field: state.get(field) for field in PRODUCT_FIELDS if field in state}
    return {"product": product} if product else None


def _listing_from_state(state: dict[str, Any]) -> dict[str, Any] | None:
    required = ["listing_price", "deal_price_min", "deal_price_max", "suggested_floor_price", "title", "description"]
    if not all(state.get(key) is not None for key in required):
        return None

    return {
        "session_id": state.get("session_id"),
        "price": {
            "listing_price": state["listing_price"],
            "deal_price_min": state["deal_price_min"],
            "deal_price_max": state["deal_price_max"],
            "suggested_floor_price": state["suggested_floor_price"],
            "price_confidence": state.get("price_confidence", "低"),
            "price_reasons": state.get("price_reasons", []),
            "price_breakdown": state.get("price_breakdown", {}),
        },
        "similar_items": state.get("similar_items", []),
        "title": state["title"],
        "description": state["description"],
        "keywords": state.get("keywords", []),
        "defect_statement": state.get("defect_statement", ""),
        "photo_suggestions": state.get("photo_suggestions", []),
        "trace": state.get("trace", []),
    }


def _view_from_step(step: str | None, has_listing: bool) -> str:
    if step == "user_confirmation":
        return "确认识别结果"
    if step in {"information_check", "ask_question", "ready_for_listing"}:
        return "补充商品信息"
    if step == "negotiation":
        return "模拟议价"
    if has_listing or step in {"price_estimation", "price_validation", "listing_generation", "listing_ready"}:
        return "出售方案"
    return "开始出售"
