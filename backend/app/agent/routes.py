from __future__ import annotations


def route_after_information_check(missing_fields: list[str]) -> str:
    if missing_fields:
        return "ask_question"
    return "search_similar_items"


def route_after_price_validation(errors: list[str]) -> str:
    if errors:
        return "estimate_price"
    return "generate_listing"

