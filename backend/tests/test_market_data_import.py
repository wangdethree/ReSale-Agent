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

    results = search_similar_items("digital", "mechanical_keyboard", "Keychron", "K2", limit=1)
    assert results[0]["source_type"] == "imported"
    assert results[0]["source_name"] == "测试授权表"
    assert results[0]["sold_price"] == 420
    assert "用户导入样本" in results[0]["match_reasons"]
