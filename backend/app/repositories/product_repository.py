from __future__ import annotations

from typing import Any

from backend.app.db.connection import get_connection
from backend.app.tools.image_similarity import build_image_query_signature, score_image_similarity


def _score_item(item: dict[str, Any], product_type: str, brand: str | None, model: str | None) -> int:
    score = 0
    if product_type and product_type.lower() in item["product_type"].lower():
        score += 5
    if brand and item.get("brand") and brand.lower() in item["brand"].lower():
        score += 4
    if model and item.get("model") and model.lower() in item["model"].lower():
        score += 6
    return score


def _text_match_reasons(item: dict[str, Any], product_type: str, brand: str | None, model: str | None) -> list[str]:
    reasons: list[str] = []
    if product_type and product_type.lower() in item["product_type"].lower():
        reasons.append("类型匹配")
    if brand and item.get("brand") and brand.lower() in item["brand"].lower():
        reasons.append("品牌匹配")
    if model and item.get("model") and model.lower() in item["model"].lower():
        reasons.append("型号匹配")
    return reasons


class ProductRepository:
    def search_similar(
        self,
        category: str,
        product_type: str,
        brand: str | None = None,
        model: str | None = None,
        limit: int = 5,
        image_paths: list[str] | None = None,
        visual_keywords: list[str] | None = None,
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
        image_signature = build_image_query_signature(image_paths, visual_keywords)
        for item in candidates:
            item["accessories_complete"] = bool(item["accessories_complete"])
            text_score = _score_item(item, product_type, brand, model)
            image_score, image_reasons = score_image_similarity(item, image_signature)
            item["text_match_score"] = text_score
            item["image_similarity_score"] = image_score
            item["match_reasons"] = [*_text_match_reasons(item, product_type, brand, model), *image_reasons]
            item["_score"] = text_score * 10 + image_score

        scored = [item for item in candidates if item["_score"] > 0]
        scored.sort(key=lambda item: (item["_score"], item["sold_price"]), reverse=True)
        results = scored[:limit]
        for item in results:
            item.pop("_score", None)
        return results
