from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.tools.product_search import search_similar_items


def test_market_data_import_feeds_local_similarity(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from backend.app.main import app

    csv_text = "\n".join(
        [
            "category,product_type,brand,model,condition_level,age_months,original_price,listing_price,sold_price,accessories_complete,description",
            "digital,mechanical_keyboard,Keychron,K2,轻微使用痕迹,6,499,455,420,true,门店授权成交样本",
            "unknown,mechanical_keyboard,Keychron,K2,轻微使用痕迹,6,499,455,420,true,错误类别",
        ]
    )

    with TestClient(app) as client:
        imported = client.post(
            "/api/v1/market-data/import",
            data={"source_name": "测试授权表"},
            files={"file": ("samples.csv", csv_text.encode("utf-8"), "text/csv")},
        )
        assert imported.status_code == 200
        import_json = imported.json()
        assert import_json["imported_count"] == 1
        assert import_json["error_count"] == 1
        assert import_json["errors"][0]["row_number"] == 3

        duplicate = client.post(
            "/api/v1/market-data/import",
            data={"source_name": "测试授权表"},
            files={"file": ("samples.csv", csv_text.encode("utf-8"), "text/csv")},
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["skipped_count"] == 1

        samples = client.get(
            "/api/v1/market-data/samples",
            params={"category": "digital", "source_type": "imported"},
        )
        assert samples.status_code == 200
        samples_json = samples.json()
        assert samples_json["total_count"] == 1
        assert samples_json["by_source_type"] == {"imported": 1}
        imported_item = samples_json["items"][0]
        assert imported_item["deletable"] is True
        assert imported_item["editable"] is True
        assert imported_item["active"] is True
        assert imported_item["source_name"] == "测试授权表"

        seed_samples = client.get(
            "/api/v1/market-data/samples",
            params={"category": "digital", "source_type": "seed", "limit": 1},
        )
        assert seed_samples.status_code == 200
        seed_item = seed_samples.json()["items"][0]
        forbidden_delete = client.delete(f"/api/v1/market-data/samples/{seed_item['id']}")
        assert forbidden_delete.status_code == 400
        forbidden_update = client.patch(
            f"/api/v1/market-data/samples/{seed_item['id']}",
            json={"active": False, "user_notes": "不应修改内置样本"},
        )
        assert forbidden_update.status_code == 400

    results = search_similar_items("digital", "mechanical_keyboard", "Keychron", "K2", limit=1)
    assert results[0]["source_type"] == "imported"
    assert results[0]["source_name"] == "测试授权表"
    assert results[0]["sold_price"] == 420
    assert "用户导入样本" in results[0]["match_reasons"]

    with TestClient(app) as client:
        disabled = client.patch(
            f"/api/v1/market-data/samples/{imported_item['id']}",
            json={"active": False, "user_notes": "价格偏高，先停用"},
        )
        assert disabled.status_code == 200
        disabled_json = disabled.json()
        assert disabled_json["active"] is False
        assert disabled_json["user_notes"] == "价格偏高，先停用"
        assert disabled_json["disabled_at"] is not None

        inactive_samples = client.get(
            "/api/v1/market-data/samples",
            params={"category": "digital", "source_type": "imported", "active": False},
        )
        assert inactive_samples.status_code == 200
        assert inactive_samples.json()["total_count"] == 1

    results_after_disable = search_similar_items("digital", "mechanical_keyboard", "Keychron", "K2", limit=1)
    assert results_after_disable[0]["source_type"] == "seed"

    with TestClient(app) as client:
        restored = client.patch(
            f"/api/v1/market-data/samples/{imported_item['id']}",
            json={"active": True, "user_notes": "复核后恢复"},
        )
        assert restored.status_code == 200
        assert restored.json()["active"] is True
        assert restored.json()["disabled_at"] is None

    results_after_restore = search_similar_items("digital", "mechanical_keyboard", "Keychron", "K2", limit=1)
    assert results_after_restore[0]["source_type"] == "imported"

    with TestClient(app) as client:
        deleted = client.delete(f"/api/v1/market-data/samples/{imported_item['id']}")
        assert deleted.status_code == 204
        samples_after_delete = client.get(
            "/api/v1/market-data/samples",
            params={"category": "digital", "source_type": "imported"},
        )
        assert samples_after_delete.status_code == 200
        assert samples_after_delete.json()["total_count"] == 0

    results_after_delete = search_similar_items("digital", "mechanical_keyboard", "Keychron", "K2", limit=1)
    assert results_after_delete[0]["source_type"] == "seed"
