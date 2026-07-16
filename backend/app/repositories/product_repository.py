from __future__ import annotations

import json
from typing import Any

from backend.app.core.exceptions import AppError
from backend.app.db.connection import get_connection
from backend.app.tools.image_similarity import build_image_query_signature, score_image_similarity


CATEGORY_LABELS = {
    "digital": "数码产品",
    "book": "图书",
    "appliance": "小家电",
    "clothing": "服装",
    "furniture": "家具",
    "shoe_bag": "鞋包",
}


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
    def list_reference_items(
        self,
        category: str | None = None,
        source_type: str | None = None,
        source_name: str | None = None,
        active: bool | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if source_type:
            clauses.append("source_type = ?")
            params.append(source_type)
        if source_name:
            clauses.append("source_name = ?")
            params.append(source_name)
        if active is not None:
            clauses.append("COALESCE(active, 1) = ?")
            params.append(1 if active else 0)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT id, category, product_type, brand, model, condition_level, age_months,
                       original_price, listing_price, sold_price, accessories_complete, description,
                       source_name, source_type, source_url, imported_at, active, user_notes, disabled_at
                FROM reference_items
                {where_sql}
                ORDER BY imported_at DESC, id DESC
                """,
                params,
            ).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            items.append(self._build_reference_item(dict(row)))

        by_source_type: dict[str, int] = {}
        by_category: dict[str, int] = {}
        by_active: dict[str, int] = {}
        for item in items:
            by_source_type[item["source_type"]] = by_source_type.get(item["source_type"], 0) + 1
            by_category[item["category"]] = by_category.get(item["category"], 0) + 1
            active_key = "active" if item["active"] else "inactive"
            by_active[active_key] = by_active.get(active_key, 0) + 1

        return {
            "total_count": len(items),
            "by_source_type": by_source_type,
            "by_category": by_category,
            "by_active": by_active,
            "items": items[:limit],
        }

    def list_sample_events(
        self,
        item_id: int | None = None,
        action: str | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []
        if item_id is not None:
            clauses.append("item_id = ?")
            params.append(item_id)
        if action:
            clauses.append("action = ?")
            params.append(action)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT id, item_id, action, category, product_type, brand, model,
                       source_name, source_type, detail_json, created_at
                FROM market_sample_events
                {where_sql}
                ORDER BY created_at DESC, id DESC
                """,
                params,
            ).fetchall()

        events: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            event["category_label"] = CATEGORY_LABELS.get(event.get("category"), event.get("category"))
            event["detail"] = json.loads(event.pop("detail_json") or "{}")
            events.append(event)
        return {"total_count": len(events), "items": events[:limit]}

    def update_reference_item(self, item_id: int, active: bool | None = None, user_notes: str | None = None) -> dict[str, Any]:
        with get_connection() as conn:
            before = self._fetch_reference_item(conn, item_id)
            if before is None:
                raise AppError("价格样本不存在", status_code=404, code="market_sample_not_found")
            if (before["source_type"] or "seed") != "imported":
                raise AppError("内置价格样本不能修改", status_code=400, code="market_sample_not_editable")

            next_active = bool(before["active"]) if active is None else active
            next_notes = before["user_notes"] if user_notes is None else user_notes.strip()
            conn.execute(
                """
                UPDATE reference_items
                SET active = ?,
                    user_notes = ?,
                    disabled_at = CASE
                        WHEN ? IS NULL THEN disabled_at
                        WHEN ? = 0 THEN CURRENT_TIMESTAMP
                        WHEN ? = 1 THEN NULL
                        ELSE disabled_at
                    END
                WHERE id = ?
                """,
                (
                    int(next_active),
                    next_notes,
                    None if active is None else int(next_active),
                    int(next_active),
                    int(next_active),
                    item_id,
                ),
            )
            after = self._fetch_reference_item(conn, item_id)
            if after is None:
                raise AppError("价格样本不存在", status_code=404, code="market_sample_not_found")
            action = self._resolve_update_action(bool(before["active"]), bool(after["active"]))
            self._record_sample_event(conn, after, action, {"before": before, "after": after})
            conn.commit()
        return self.get_reference_item(item_id)

    def get_reference_item(self, item_id: int) -> dict[str, Any]:
        result = self.list_reference_items(limit=1_000_000)
        for item in result["items"]:
            if int(item["id"]) == item_id:
                return item
        raise AppError("价格样本不存在", status_code=404, code="market_sample_not_found")

    def delete_reference_item(self, item_id: int) -> None:
        with get_connection() as conn:
            row = self._fetch_reference_item(conn, item_id)
            if row is None:
                raise AppError("价格样本不存在", status_code=404, code="market_sample_not_found")
            if (row["source_type"] or "seed") != "imported":
                raise AppError("内置价格样本不能删除", status_code=400, code="market_sample_not_deletable")
            self._record_sample_event(conn, row, "delete", {"before": row})
            conn.execute("DELETE FROM reference_items WHERE id = ?", (item_id,))
            conn.commit()

    def import_reference_items(self, items: list[dict[str, Any]]) -> dict[str, int]:
        imported_count = 0
        skipped_count = 0
        with get_connection() as conn:
            for item in items:
                existing = conn.execute(
                    """
                    SELECT id
                    FROM reference_items
                    WHERE category = ?
                      AND product_type = ?
                      AND COALESCE(brand, '') = COALESCE(?, '')
                      AND COALESCE(model, '') = COALESCE(?, '')
                      AND condition_level = ?
                      AND sold_price = ?
                      AND description = ?
                    LIMIT 1
                    """,
                    (
                        item["category"],
                        item["product_type"],
                        item.get("brand"),
                        item.get("model"),
                        item["condition_level"],
                        item["sold_price"],
                        item["description"],
                    ),
                ).fetchone()
                if existing:
                    skipped_count += 1
                    continue

                cursor = conn.execute(
                    """
                    INSERT INTO reference_items (
                        category, product_type, brand, model, condition_level, age_months,
                        original_price, listing_price, sold_price, accessories_complete, description,
                        source_name, source_type, source_url, imported_at, active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                    """,
                    (
                        item["category"],
                        item["product_type"],
                        item.get("brand"),
                        item.get("model"),
                        item["condition_level"],
                        item["age_months"],
                        item["original_price"],
                        item["listing_price"],
                        item["sold_price"],
                        int(item["accessories_complete"]),
                        item["description"],
                        item.get("source_name") or "用户导入 CSV",
                        item.get("source_type") or "imported",
                        item.get("source_url"),
                    ),
                )
                event_item = self._build_reference_item(
                    {
                        **item,
                        "id": cursor.lastrowid,
                        "active": 1,
                        "user_notes": None,
                        "disabled_at": None,
                        "imported_at": None,
                    }
                )
                self._record_sample_event(conn, event_item, "import", {"after": event_item})
                imported_count += 1
            conn.commit()
        return {"imported_count": imported_count, "skipped_count": skipped_count}

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
                       original_price, listing_price, sold_price, accessories_complete, description,
                       source_name, source_type, source_url
                FROM reference_items
                WHERE category = ? AND COALESCE(active, 1) = 1
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
            if item.get("source_type") == "imported":
                item["match_reasons"].append("用户导入样本")
            item["_score"] = text_score * 10 + image_score

        scored = [item for item in candidates if item["_score"] > 0]
        scored.sort(key=lambda item: (item["_score"], item["sold_price"]), reverse=True)
        results = scored[:limit]
        for item in results:
            item.pop("_score", None)
        return results

    def _fetch_reference_item(self, conn: Any, item_id: int) -> dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT id, category, product_type, brand, model, condition_level, age_months,
                   original_price, listing_price, sold_price, accessories_complete, description,
                   source_name, source_type, source_url, imported_at, active, user_notes, disabled_at
            FROM reference_items
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
        if row is None:
            return None
        return self._build_reference_item(dict(row))

    def _build_reference_item(self, item: dict[str, Any]) -> dict[str, Any]:
        item["category_label"] = CATEGORY_LABELS.get(item["category"], item["category"])
        item["accessories_complete"] = bool(item["accessories_complete"])
        item["source_name"] = item.get("source_name") or "内置模拟数据"
        item["source_type"] = item.get("source_type") or "seed"
        item["active"] = bool(item.get("active", 1))
        item["deletable"] = item["source_type"] == "imported"
        item["editable"] = item["source_type"] == "imported"
        return item

    def _record_sample_event(self, conn: Any, item: dict[str, Any], action: str, detail: dict[str, Any]) -> None:
        conn.execute(
            """
            INSERT INTO market_sample_events (
                item_id, action, category, product_type, brand, model,
                source_name, source_type, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("id"),
                action,
                item.get("category"),
                item.get("product_type"),
                item.get("brand"),
                item.get("model"),
                item.get("source_name"),
                item.get("source_type"),
                json.dumps(detail, ensure_ascii=False),
            ),
        )

    def _resolve_update_action(self, before_active: bool, after_active: bool) -> str:
        if before_active and not after_active:
            return "disable"
        if not before_active and after_active:
            return "restore"
        return "update"
