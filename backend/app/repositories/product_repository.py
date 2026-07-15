from __future__ import annotations

from typing import Any

from backend.app.db.connection import get_connection


def _score_item(item: dict[str, Any], product_type: str, brand: str | None, model: str | None) -> int:
    score = 0
    if product_type and product_type.lower() in item["product_type"].lower():
        score += 5
    if brand and item.get("brand") and brand.lower() in item["brand"].lower():
        score += 4
    if model and item.get("model") and model.lower() in item["model"].lower():
        score += 6
    return score


class ProductRepository:
    def search_similar(
        self,
        category: str,
        product_type: str,
        brand: str | None = None,
        model: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, category, product_type, brand, model, condition_level, age_months,
                       original_price, listing_price, sold_price, accessories_complete, description
                FROM reference_items
                WHERE category = ?
                """,
                (category,),
            ).fetchall()

        candidates = [dict(row) for row in rows]
        for item in candidates:
            item["accessories_complete"] = bool(item["accessories_complete"])
            item["_score"] = _score_item(item, product_type, brand, model)

        scored = [item for item in candidates if item["_score"] > 0]
        scored.sort(key=lambda item: (item["_score"], item["sold_price"]), reverse=True)
        results = scored[:limit]
        for item in results:
            item.pop("_score", None)
        return results

