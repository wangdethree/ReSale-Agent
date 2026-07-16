from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from backend.app.core.exceptions import AppError
from backend.app.db.connection import get_connection


CATEGORY_LABELS = {
    "digital": "数码产品",
    "book": "图书",
    "appliance": "小家电",
    "clothing": "服装",
    "furniture": "家具",
    "shoe_bag": "鞋包",
}


class SessionRepository:
    def create(self, category: str) -> dict[str, Any]:
        session_id = str(uuid4())
        state: dict[str, Any] = {
            "session_id": session_id,
            "category": category,
            "current_step": "start",
            "confirmed": False,
            "visible_defects": [],
            "accessories": [],
            "additional_defects": [],
            "user_answers": {},
            "missing_fields": [],
            "similar_items": [],
            "price_reasons": [],
            "price_breakdown": {},
            "keywords": [],
            "photo_suggestions": [],
            "platform_copies": [],
            "inventory_status": "draft",
            "storage_location": None,
            "inventory_notes": None,
            "listing_performance": None,
            "reprice_suggestion": None,
            "sale_outcome": None,
            "errors": [],
            "trace": [],
        }
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sale_sessions (id, category, current_step, state_json)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, category, state["current_step"], json.dumps(state, ensure_ascii=False)),
            )
            conn.commit()
        return state

    def get(self, session_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT state_json FROM sale_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            raise AppError("出售会话不存在", status_code=404, code="session_not_found")
        return json.loads(row["state_json"])

    def save(self, state: dict[str, Any]) -> dict[str, Any]:
        state["current_step"] = state.get("current_step", "start")
        with get_connection() as conn:
            result = conn.execute(
                """
                UPDATE sale_sessions
                SET current_step = ?, state_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    state["current_step"],
                    json.dumps(state, ensure_ascii=False),
                    state["session_id"],
                ),
            )
            if result.rowcount == 0:
                raise AppError("出售会话不存在", status_code=404, code="session_not_found")
            conn.commit()
        return state

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, category, current_step, state_json, created_at, updated_at
                FROM sale_sessions
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        summaries: list[dict[str, Any]] = []
        for row in rows:
            state = json.loads(row["state_json"])
            summaries.append(
                {
                    "session_id": row["id"],
                    "category": row["category"],
                    "current_step": row["current_step"],
                    "product_label": self._product_label(state),
                    "inventory_status": self._inventory_status(state),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )
        return summaries

    def inventory_summary(
        self,
        category: str | None = None,
        inventory_status: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, category, state_json, updated_at
                FROM sale_sessions
                ORDER BY updated_at DESC
                """,
            ).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            state = json.loads(row["state_json"])
            status = self._inventory_status(state)
            if category and row["category"] != category:
                continue
            if inventory_status and status != inventory_status:
                continue
            performance = state.get("listing_performance") or {}
            suggestion = state.get("reprice_suggestion") or {}
            items.append(
                {
                    "session_id": row["id"],
                    "category": row["category"],
                    "category_label": CATEGORY_LABELS.get(row["category"], row["category"]),
                    "product_label": self._product_label(state),
                    "inventory_status": status,
                    "listing_price": state.get("listing_price"),
                    "suggested_floor_price": state.get("suggested_floor_price"),
                    "days_listed": performance.get("days_listed"),
                    "view_count": performance.get("view_count"),
                    "favorite_count": performance.get("favorite_count"),
                    "inquiry_count": performance.get("inquiry_count"),
                    "next_action": suggestion.get("next_action"),
                    "updated_at": row["updated_at"],
                }
            )

        visible_items = items[:limit]
        by_status: dict[str, int] = {}
        for item in items:
            status = item["inventory_status"]
            by_status[status] = by_status.get(status, 0) + 1
        return {"total_count": len(items), "by_status": by_status, "items": visible_items}

    def outcome_summary(
        self,
        recent_limit: int = 8,
        category: str | None = None,
        sold_channel: str | None = None,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, category, state_json, updated_at
                FROM sale_sessions
                ORDER BY updated_at DESC
                """
            ).fetchall()

        outcomes: list[dict[str, Any]] = []
        for row in rows:
            state = json.loads(row["state_json"])
            outcome = state.get("sale_outcome")
            if not outcome:
                continue
            if category and row["category"] != category:
                continue
            if sold_channel and (outcome.get("sold_channel") or "未填写") != sold_channel:
                continue
            outcomes.append(
                {
                    "session_id": row["id"],
                    "category": row["category"],
                    "product_label": self._product_label(state),
                    "final_sold_price": float(outcome["final_sold_price"]),
                    "sold_channel": outcome.get("sold_channel") or "未填写",
                    "price_position": outcome.get("price_position") or "暂无",
                    "price_delta_from_mid": outcome.get("price_delta_from_mid"),
                    "price_delta_rate": outcome.get("price_delta_rate"),
                    "updated_at": row["updated_at"],
                }
            )

        total_count = len(outcomes)
        in_range_count = sum(1 for item in outcomes if item["price_position"] == "符合估价区间")
        deltas = [float(item["price_delta_from_mid"]) for item in outcomes if item["price_delta_from_mid"] is not None]
        delta_rates = [float(item["price_delta_rate"]) for item in outcomes if item["price_delta_rate"] is not None]
        total_sold_amount = sum(item["final_sold_price"] for item in outcomes)

        return {
            "total_count": total_count,
            "in_range_count": in_range_count,
            "in_range_rate": round(in_range_count / total_count, 4) if total_count else 0.0,
            "average_delta_from_mid": round(sum(deltas) / len(deltas), 2) if deltas else None,
            "average_delta_rate": round(sum(delta_rates) / len(delta_rates), 4) if delta_rates else None,
            "total_sold_amount": round(total_sold_amount, 2),
            "by_category": self._summarize_outcomes_by_category(outcomes),
            "recent_outcomes": outcomes[:recent_limit],
        }

    def delete(self, session_id: str) -> None:
        with get_connection() as conn:
            result = conn.execute("DELETE FROM sale_sessions WHERE id = ?", (session_id,))
            if result.rowcount == 0:
                raise AppError("出售会话不存在", status_code=404, code="session_not_found")
            conn.commit()

    def record_negotiation(self, session_id: str, buyer_message: str, intent: str, reply: str) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO negotiation_messages (session_id, buyer_message, intent, suggested_reply)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, buyer_message, intent, reply),
            )
            conn.commit()

    def _product_label(self, state: dict[str, Any]) -> str:
        title = str(state.get("title") or "").strip()
        if title:
            return title[:60]
        parts = [
            str(state.get("brand") or "").strip(),
            str(state.get("model") or state.get("product_type") or "").strip(),
        ]
        label = " ".join(part for part in parts if part).strip()
        return label[:60] if label else "未命名草稿"

    def _inventory_status(self, state: dict[str, Any]) -> str:
        if state.get("sale_outcome"):
            return "sold"
        return state.get("inventory_status") or ("ready" if state.get("listing_price") else "draft")

    def _summarize_outcomes_by_category(self, outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for category, category_label in CATEGORY_LABELS.items():
            items = [item for item in outcomes if item["category"] == category]
            if not items:
                continue

            in_range_count = sum(1 for item in items if item["price_position"] == "符合估价区间")
            deltas = [float(item["price_delta_from_mid"]) for item in items if item["price_delta_from_mid"] is not None]
            delta_rates = [float(item["price_delta_rate"]) for item in items if item["price_delta_rate"] is not None]
            total_sold_amount = sum(item["final_sold_price"] for item in items)
            summaries.append(
                {
                    "category": category,
                    "category_label": category_label,
                    "total_count": len(items),
                    "in_range_count": in_range_count,
                    "in_range_rate": round(in_range_count / len(items), 4),
                    "average_delta_from_mid": round(sum(deltas) / len(deltas), 2) if deltas else None,
                    "average_delta_rate": round(sum(delta_rates) / len(delta_rates), 4) if delta_rates else None,
                    "total_sold_amount": round(total_sold_amount, 2),
                }
            )
        return summaries
