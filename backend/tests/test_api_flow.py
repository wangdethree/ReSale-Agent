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
        platform_copies = listing_json["platform_copies"]
        assert {item["platform"] for item in platform_copies} == {"xianyu", "zhuanzhuan", "xiaohongshu"}
        assert all("空格键轻微划痕" in item["body"] for item in platform_copies)

        floor = listing_json["price"]["suggested_floor_price"]
        negotiation = client.post(
            f"/api/v1/sessions/{session_id}/negotiation/reply",
            json={"buyer_message": "150 包邮行不行", "user_floor_price": floor},
        )
        assert negotiation.status_code == 200
        assert negotiation.json()["below_floor_price"] is True
        assert str(floor) in negotiation.json()["suggested_reply"]

        outcome = client.post(
            f"/api/v1/sessions/{session_id}/outcome",
            json={"final_sold_price": 280, "sold_channel": "闲鱼", "sale_notes": "两天内成交"},
        )
        assert outcome.status_code == 200
        sale_outcome = outcome.json()["state"]["sale_outcome"]
        assert sale_outcome["final_sold_price"] == 280
        assert sale_outcome["sold_channel"] == "闲鱼"
        assert sale_outcome["price_position"] == "符合估价区间"
        assert sale_outcome["price_delta_from_mid"] != 0

        outcome_summary = client.get("/api/v1/sessions/outcomes/summary")
        assert outcome_summary.status_code == 200
        summary_json = outcome_summary.json()
        assert summary_json["total_count"] == 1
        assert summary_json["in_range_count"] == 1
        assert summary_json["recent_outcomes"][0]["session_id"] == session_id
        assert summary_json["recent_outcomes"][0]["final_sold_price"] == 280

        exported = client.get(f"/api/v1/sessions/{session_id}/export")
        assert exported.status_code == 200
        assert "# 闲置 Keychron K2" in exported.text
        assert "## 估价拆解" in exported.text
        assert "## 多平台文案" in exported.text
        assert "### 闲鱼" in exported.text
        assert "## 成交反馈" in exported.text
        assert "两天内成交" in exported.text

        sessions = client.get("/api/v1/sessions")
        assert sessions.status_code == 200
        summaries = sessions.json()
        assert any(item["session_id"] == session_id and "Keychron" in item["product_label"] for item in summaries)

        deleted = client.delete(f"/api/v1/sessions/{session_id}")
        assert deleted.status_code == 204
        assert client.get(f"/api/v1/sessions/{session_id}").status_code == 404
        assert client.get("/api/v1/sessions/outcomes/summary").json()["total_count"] == 0
