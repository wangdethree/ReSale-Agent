from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


DEMO_CASES_PATH = Path(__file__).resolve().parents[2] / "data" / "demo_cases.json"


def load_demo_cases() -> list[dict[str, Any]]:
    with DEMO_CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.parametrize("case", load_demo_cases(), ids=lambda case: case["name"])
def test_demo_case_full_flow(monkeypatch, tmp_path, case: dict[str, Any]) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    monkeypatch.setenv("RESALE_AGENT_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from backend.app.main import app

    with TestClient(app) as client:
        created = client.post("/api/v1/sessions", json={"category": case["category"]})
        assert created.status_code == 200
        session_id = created.json()["session_id"]

        confirmed = client.post(
            f"/api/v1/sessions/{session_id}/confirm",
            json={"product": case["product"]},
        )
        assert confirmed.status_code == 200

        question = client.get(f"/api/v1/sessions/{session_id}/questions/next")
        assert question.status_code == 200
        assert question.json()["completed"] is True

        listing = client.post(f"/api/v1/sessions/{session_id}/listing/generate")
        assert listing.status_code == 200
        listing_json = listing.json()
        assert case["expected_title_keyword"] in listing_json["title"]
        assert listing_json["similar_items"]
        assert listing_json["price"]["listing_price"] >= listing_json["price"]["deal_price_max"]

        floor_price = listing_json["price"]["suggested_floor_price"]
        negotiation = client.post(
            f"/api/v1/sessions/{session_id}/negotiation/reply",
            json={"buyer_message": case["buyer_message"], "user_floor_price": floor_price},
        )
        assert negotiation.status_code == 200
        assert negotiation.json()["suggested_reply"]

        exported = client.get(f"/api/v1/sessions/{session_id}/export")
        assert exported.status_code == 200
        assert listing_json["title"] in exported.text
