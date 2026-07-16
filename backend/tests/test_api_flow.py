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
        checklist = listing_json["publish_checklist"]
        assert checklist
        assert {item["status"] for item in checklist} <= {"done", "review", "todo"}
        assert any(item["item_id"] == "price" and item["status"] == "done" for item in checklist)
        assert listing_json["inventory_status"] == "ready"
        floor = listing_json["price"]["suggested_floor_price"]

        inventory_update = client.post(
            f"/api/v1/sessions/{session_id}/inventory",
            json={
                "inventory_status": "listed",
                "storage_location": "书房置物架",
                "inventory_notes": "已清洁，待买家确认",
            },
        )
        assert inventory_update.status_code == 200
        inventory_state = inventory_update.json()["state"]
        assert inventory_state["inventory_status"] == "listed"
        assert inventory_state["storage_location"] == "书房置物架"

        performance = client.post(
            f"/api/v1/sessions/{session_id}/performance",
            json={
                "days_listed": 5,
                "view_count": 120,
                "favorite_count": 1,
                "inquiry_count": 0,
                "current_listing_price": listing_json["price"]["listing_price"],
            },
        )
        assert performance.status_code == 200
        performance_state = performance.json()["state"]
        assert performance_state["listing_performance"]["view_count"] == 120
        assert performance_state["reprice_suggestion"]["recommended_listing_price"] >= floor
        assert performance_state["reprice_suggestion"]["next_action"] in {"降价 5%", "小幅降价 3%", "保持价格", "优化展示", "继续观察"}

        inventory_summary = client.get("/api/v1/sessions/inventory/summary", params={"inventory_status": "listed"})
        assert inventory_summary.status_code == 200
        assert inventory_summary.json()["total_count"] == 1

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
        assert outcome.json()["state"]["inventory_status"] == "sold"

        outcome_summary = client.get("/api/v1/sessions/outcomes/summary")
        assert outcome_summary.status_code == 200
        summary_json = outcome_summary.json()
        assert summary_json["total_count"] == 1
        assert summary_json["in_range_count"] == 1
        assert summary_json["by_category"][0]["category"] == "digital"
        assert summary_json["by_category"][0]["total_count"] == 1
        assert summary_json["by_category"][0]["in_range_count"] == 1
        assert summary_json["recent_outcomes"][0]["session_id"] == session_id
        assert summary_json["recent_outcomes"][0]["final_sold_price"] == 280
        filtered_summary = client.get(
            "/api/v1/sessions/outcomes/summary",
            params={"category": "digital", "sold_channel": "闲鱼"},
        )
        assert filtered_summary.status_code == 200
        assert filtered_summary.json()["total_count"] == 1
        empty_channel_summary = client.get(
            "/api/v1/sessions/outcomes/summary",
            params={"category": "digital", "sold_channel": "转转"},
        )
        assert empty_channel_summary.status_code == 200
        assert empty_channel_summary.json()["total_count"] == 0

        exported = client.get(f"/api/v1/sessions/{session_id}/export")
        assert exported.status_code == 200
        assert "# 闲置 Keychron K2" in exported.text
        assert "## 估价拆解" in exported.text
        assert "调价明细" in exported.text
        assert "## 多平台文案" in exported.text
        assert "## 发布前检查" in exported.text
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
        assert client.get("/api/v1/sessions/outcomes/summary").json()["by_category"] == []


def test_image_upload_keeps_original_names_for_local_similarity(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    monkeypatch.setenv("RESALE_AGENT_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from backend.app.main import app

    with TestClient(app) as client:
        created = client.post("/api/v1/sessions", json={"category": "shoe_bag"})
        assert created.status_code == 200
        session_id = created.json()["session_id"]

        analyzed = client.post(
            f"/api/v1/sessions/{session_id}/images/analyze",
            files={"files": ("nike_airforce_photo.jpg", b"fake image bytes", "image/jpeg")},
        )
        assert analyzed.status_code == 200

        state = client.get(f"/api/v1/sessions/{session_id}").json()["state"]
        assert state["image_original_names"] == ["nike_airforce_photo.jpg"]

        confirmed = client.post(
            f"/api/v1/sessions/{session_id}/confirm",
            json={
                "product": {
                    "category": "shoe_bag",
                    "product_type": "shoe_bag",
                    "brand": "不确定",
                    "model": "不确定",
                    "visible_condition": "轻微使用痕迹",
                    "visible_defects": ["鞋底正常磨损"],
                    "original_price": 749,
                    "purchase_date": "2024-08",
                    "size": "42",
                    "material": "皮革鞋面",
                    "wear_status": "正常穿着痕迹",
                    "clean_status": "已简单清洁",
                    "authenticity_status": "支持当面验货",
                    "accessories": ["鞋盒"],
                    "additional_defects": ["无其他明显瑕疵"],
                    "delivery_options": "支持邮寄或同城验货",
                }
            },
        )
        assert confirmed.status_code == 200

        listing = client.post(f"/api/v1/sessions/{session_id}/listing/generate")
        assert listing.status_code == 200
        listing_json = listing.json()
        assert listing_json["similar_items"][0]["brand"] == "Nike"
        assert listing_json["similar_items"][0]["image_similarity_score"] > 0
        assert listing_json["price"]["price_breakdown"]["image_similarity_used"] is True
        assert any(item["item_id"] == "shoe_bag_authenticity" for item in listing_json["publish_checklist"])
