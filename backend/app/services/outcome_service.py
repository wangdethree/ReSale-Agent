from __future__ import annotations

from typing import Any


class OutcomeService:
    def record(
        self,
        state: dict[str, Any],
        final_sold_price: float,
        sold_channel: str | None,
        sale_notes: str | None,
    ) -> dict[str, Any]:
        final_price = round(float(final_sold_price), 2)
        deal_min = self._to_float(state.get("deal_price_min"))
        deal_max = self._to_float(state.get("deal_price_max"))
        range_mid = (deal_min + deal_max) / 2 if deal_min is not None and deal_max is not None else None
        delta = round(final_price - range_mid, 2) if range_mid else None
        delta_rate = round(delta / range_mid, 4) if delta is not None and range_mid else None

        state["sale_outcome"] = {
            "final_sold_price": final_price,
            "sold_channel": (sold_channel or "未填写").strip() or "未填写",
            "sale_notes": (sale_notes or "").strip(),
            "deal_price_min": deal_min,
            "deal_price_max": deal_max,
            "listing_price": self._to_float(state.get("listing_price")),
            "suggested_floor_price": self._to_float(state.get("suggested_floor_price")),
            "price_delta_from_mid": delta,
            "price_delta_rate": delta_rate,
            "price_position": self._price_position(final_price, deal_min, deal_max),
        }
        state["current_step"] = "sold_feedback"
        return state

    def _price_position(self, final_price: float, deal_min: float | None, deal_max: float | None) -> str:
        if deal_min is None or deal_max is None:
            return "暂无估价区间"
        if final_price < deal_min:
            return "低于估价区间"
        if final_price > deal_max:
            return "高于估价区间"
        return "符合估价区间"

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value), 2)
