from __future__ import annotations

from typing import Any


STATUS_LABELS = {
    "draft": "草稿",
    "ready": "待发布",
    "listed": "已发布",
    "sold": "已成交",
    "archived": "已归档",
}


class InventoryService:
    def update_status(
        self,
        state: dict[str, Any],
        inventory_status: str,
        storage_location: str | None = None,
        inventory_notes: str | None = None,
    ) -> dict[str, Any]:
        state["inventory_status"] = inventory_status
        if storage_location is not None:
            state["storage_location"] = storage_location.strip()
        if inventory_notes is not None:
            state["inventory_notes"] = inventory_notes.strip()
        state["inventory_label"] = STATUS_LABELS.get(inventory_status, inventory_status)
        return state

    def record_performance(
        self,
        state: dict[str, Any],
        *,
        days_listed: int,
        view_count: int,
        favorite_count: int,
        inquiry_count: int,
        current_listing_price: float | None = None,
    ) -> dict[str, Any]:
        price = round(float(current_listing_price or state.get("listing_price") or 0), 2)
        floor_price = self._to_float(state.get("suggested_floor_price")) or 0
        performance = {
            "days_listed": int(days_listed),
            "view_count": int(view_count),
            "favorite_count": int(favorite_count),
            "inquiry_count": int(inquiry_count),
            "current_listing_price": price,
            "interest_score": self._interest_score(view_count, favorite_count, inquiry_count),
        }
        suggestion = self._suggest_reprice(performance, price, floor_price)
        state["listing_performance"] = performance
        state["reprice_suggestion"] = suggestion
        if state.get("inventory_status") in {None, "draft", "ready"}:
            state["inventory_status"] = "listed"
        return state

    def _suggest_reprice(self, performance: dict[str, Any], current_price: float, floor_price: float) -> dict[str, Any]:
        # 本地 V3 只做保守建议，不替用户自动改价，也不低于最低接受价。
        days = int(performance["days_listed"])
        views = int(performance["view_count"])
        favorites = int(performance["favorite_count"])
        inquiries = int(performance["inquiry_count"])

        if days <= 2:
            action = "继续观察"
            reason = "发布时间较短，先观察曝光和咨询变化。"
            target_price = current_price
        elif inquiries >= 3:
            action = "保持价格"
            reason = "咨询量较高，优先提高回复速度和交易确定性。"
            target_price = current_price
        elif views >= 80 and favorites <= 1 and inquiries == 0:
            action = "降价 5%"
            reason = "曝光较高但收藏和咨询偏低，当前价格或首图吸引力可能不足。"
            target_price = current_price * 0.95
        elif favorites >= 3 and inquiries == 0:
            action = "小幅降价 3%"
            reason = "收藏较多但咨询不足，可以小幅让价或补充细节图推动决策。"
            target_price = current_price * 0.97
        elif views < 20 and days >= 3:
            action = "优化展示"
            reason = "曝光不足，优先优化标题关键词、主图和发布时间，不急于降价。"
            target_price = current_price
        else:
            action = "保持价格"
            reason = "曝光、收藏和咨询暂未显示明显异常。"
            target_price = current_price

        guarded_price = max(floor_price, round(target_price))
        return {
            "next_action": action,
            "reason": reason,
            "recommended_listing_price": guarded_price,
            "price_floor_guard": floor_price,
            "price_delta": round(guarded_price - current_price, 2),
        }

    def _interest_score(self, view_count: int, favorite_count: int, inquiry_count: int) -> float:
        return round(view_count * 0.1 + favorite_count * 2 + inquiry_count * 4, 2)

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value), 2)
