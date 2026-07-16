from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from backend.app.core.exceptions import AppError
from backend.app.db.connection import get_connection


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
