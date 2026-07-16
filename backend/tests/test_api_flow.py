from __future__ import annotations

from fastapi.testclient import TestClient


def test_complete_api_flow(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from backend.app.main import app

    with TestClient(app) as client:
        created = client.post("/api/v1/sessions", json={"category": "digital"})
        assert created.status_code == 200
        session_id = created.json()["session_id"]

        confirm = client.post(
            f"/api/v1/sessions/{session_id}/confirm",
            json={
                "product": {
                    "category": "digital",
                    "product_type": "mechanical_keyboard",
                    "brand": "Keychron",
                    "model": "K2",
                    "color": "gray",
                    "visible_condition": "轻微使用痕迹",
                    "visible_defects": ["空格键轻微划痕"],
                    "vision_confidence": 0.86,
                    "original_price": 499,
                    "purchase_date": "2024-05",
                    "functional_status": "功能正常",
                    "repair_history": "无维修、无进水",
                    "accessories": ["原包装", "数据线"],
                    "additional_defects": ["无"],
                }
            },
        )
        assert confirm.status_code == 200

        question = client.get(f"/api/v1/sessions/{session_id}/questions/next")
        assert question.status_code == 200
        assert question.json()["completed"] is True

        listing = client.post(f"/api/v1/sessions/{session_id}/listing/generate")
        assert listing.status_code == 200
        listing_json = listing.json()
        assert listing_json["price"]["listing_price"] >= listing_json["price"]["deal_price_max"]
        assert listing_json["price"]["price_breakdown"]["market_sample_count"] >= 3
        assert listing_json["price"]["price_breakdown"]["base_price"] > 0
        assert "Keychron" in listing_json["title"]

        floor = listing_json["price"]["suggested_floor_price"]
        negotiation = client.post(
            f"/api/v1/sessions/{session_id}/negotiation/reply",
            json={"buyer_message": "150 包邮行不行", "user_floor_price": floor},
        )
        assert negotiation.status_code == 200
        assert negotiation.json()["below_floor_price"] is True
        assert str(floor) in negotiation.json()["suggested_reply"]

        exported = client.get(f"/api/v1/sessions/{session_id}/export")
        assert exported.status_code == 200
        assert "# 闲置 Keychron K2" in exported.text
        assert "## 估价拆解" in exported.text
