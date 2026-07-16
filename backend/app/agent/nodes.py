from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any, Callable

from backend.app.services.listing_service import ListingService
from backend.app.services.negotiation_service import NegotiationService
from backend.app.services.pricing_service import PricingService
from backend.app.services.vision_service import VisionService
from backend.app.tools.field_checker import find_missing_fields, get_question_for_field
from backend.app.tools.price_calculator import validate_price_result
from backend.app.tools.product_search import search_similar_items


def _run_node(state: dict[str, Any], name: str, uses_model: bool, fn: Callable[[], None]) -> dict[str, Any]:
    started = perf_counter()
    trace = state.setdefault("trace", [])
    event = {
        "node": name,
        "started_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "uses_model": uses_model,
        "success": False,
    }
    try:
        fn()
        event["success"] = True
    except Exception as exc:
        state.setdefault("errors", []).append(f"{name}: {exc}")
        event["error"] = str(exc)
        raise
    finally:
        event["duration_ms"] = round((perf_counter() - started) * 1000, 2)
        trace.append(event)
    return state


def analyze_images_node(state: dict[str, Any], image_paths: list[str]) -> dict[str, Any]:
    def work() -> None:
        product = VisionService().analyze_images(state["category"], image_paths)
        state.update(product.model_dump(exclude_none=True))
        state["image_paths"] = image_paths
        state["current_step"] = "user_confirmation"

    return _run_node(state, "analyze_images", True, work)


def confirm_product_node(state: dict[str, Any], product_data: dict[str, Any]) -> dict[str, Any]:
    def work() -> None:
        for key, value in product_data.items():
            if value is not None:
                state[key] = value
        state["confirmed"] = True
        state["current_step"] = "information_check"

    return _run_node(state, "confirm_product", False, work)


def check_required_fields_node(state: dict[str, Any]) -> dict[str, Any]:
    def work() -> None:
        missing = find_missing_fields(state["category"], state)
        state["missing_fields"] = missing
        state["current_step"] = "ask_question" if missing else "ready_for_listing"

    return _run_node(state, "check_required_fields", False, work)


def generate_question_node(state: dict[str, Any]) -> dict[str, Any]:
    def work() -> None:
        missing = state.get("missing_fields", [])
        field = missing[0] if missing else None
        state["current_question"] = get_question_for_field(field) if field else None
        state["current_step"] = "ask_question" if field else "ready_for_listing"

    return _run_node(state, "generate_question", False, work)


def search_similar_items_node(state: dict[str, Any]) -> dict[str, Any]:
    def work() -> None:
        state["similar_items"] = search_similar_items(
            category=state["category"],
            product_type=state.get("product_type") or "",
            brand=state.get("brand"),
            model=state.get("model"),
            limit=5,
            image_paths=state.get("image_paths", []),
            visual_keywords=_visual_keywords_from_state(state),
        )
        image_scores = [int(item.get("image_similarity_score") or 0) for item in state["similar_items"]]
        state["image_similarity_summary"] = {
            "used": any(score > 0 for score in image_scores),
            "max_score": max(image_scores) if image_scores else 0,
            "image_count": len(state.get("image_paths", [])),
        }
        state["current_step"] = "price_estimation"

    return _run_node(state, "search_similar_items", False, work)


def estimate_price_node(state: dict[str, Any]) -> dict[str, Any]:
    def work() -> None:
        result = PricingService().estimate(state, state.get("similar_items", []))
        state.update(result)
        state["current_step"] = "price_validation"

    return _run_node(state, "estimate_price", False, work)


def _visual_keywords_from_state(state: dict[str, Any]) -> list[str]:
    keywords: list[str] = []
    for field in ["color", "visible_condition", "material", "size", "clean_status", "authenticity_status"]:
        value = state.get(field)
        if value:
            keywords.append(str(value))
    keywords.extend(str(item) for item in state.get("visible_defects", []) if str(item).strip())
    keywords.extend(str(item) for item in state.get("image_original_names", []) if str(item).strip())
    return keywords


def validate_price_node(state: dict[str, Any]) -> dict[str, Any]:
    def work() -> None:
        result = {
            "listing_price": state.get("listing_price", 0),
            "deal_price_min": state.get("deal_price_min", 0),
            "deal_price_max": state.get("deal_price_max", 0),
            "suggested_floor_price": state.get("suggested_floor_price", 0),
        }
        errors = validate_price_result(result)
        state["price_validation_errors"] = errors
        state["current_step"] = "listing_generation" if not errors else "price_estimation"

    return _run_node(state, "validate_price", False, work)


def generate_listing_node(state: dict[str, Any]) -> dict[str, Any]:
    def work() -> None:
        listing = ListingService().generate(state)
        state.update(listing)
        state["current_step"] = "listing_ready"

    return _run_node(state, "generate_listing", True, work)


def handle_negotiation_node(
    state: dict[str, Any],
    buyer_message: str,
    user_floor_price: float | None = None,
) -> dict[str, Any]:
    def work() -> None:
        result = NegotiationService().handle(state, buyer_message, user_floor_price)
        state.update(
            {
                "buyer_message": buyer_message,
                "buyer_intent": result["buyer_intent"],
                "suggested_reply": result["suggested_reply"],
                "user_floor_price": user_floor_price or state.get("user_floor_price"),
                "current_step": "negotiation",
            }
        )
        state["last_negotiation"] = result

    return _run_node(state, "handle_negotiation", True, work)
