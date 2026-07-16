from __future__ import annotations

from typing import Any

from backend.app.tools.price_calculator import calculate_age_months, calculate_price_range, parse_repair_history


def _list_has_value(values: Any) -> bool:
    if isinstance(values, list):
        return any(str(item).strip() for item in values)
    if isinstance(values, str):
        return bool(values.strip()) and values.strip() not in {"无", "没有", "不齐全"}
    return bool(values)


class PricingService:
    def estimate(self, state: dict[str, Any], similar_items: list[dict[str, Any]]) -> dict[str, Any]:
        original_price = float(state.get("original_price") or 0)
        age_months = calculate_age_months(state.get("purchase_date"))
        condition = state.get("visible_condition") or "轻微使用痕迹"
        functional_status = state.get("functional_status") or state.get("wear_status") or "功能正常"
        accessories_complete = _list_has_value(state.get("accessories"))
        has_repair_history = parse_repair_history(state.get("repair_history"))
        similar_prices = [float(item["sold_price"]) for item in similar_items]

        result = calculate_price_range(
            original_price=original_price,
            age_months=age_months,
            condition_level=condition,
            functional_status=functional_status,
            accessories_complete=accessories_complete,
            has_repair_history=has_repair_history,
            similar_prices=similar_prices,
        )
        image_summary = state.get("image_similarity_summary") or {}
        if image_summary.get("used"):
            result["price_reasons"].append("相似样本排序参考了本地图片线索，但成交价仍来自本地模拟数据")
            result["price_breakdown"]["image_similarity_used"] = True
            result["price_breakdown"]["image_similarity_max_score"] = image_summary.get("max_score", 0)
        else:
            result["price_breakdown"]["image_similarity_used"] = False
        return result
