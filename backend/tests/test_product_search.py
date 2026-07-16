from __future__ import annotations

from backend.app.db.init_db import init_database
from backend.app.tools.product_search import search_similar_items


def test_search_similar_items_respects_limit(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    init_database()

    results = search_similar_items(
        category="digital",
        product_type="mechanical_keyboard",
        brand="Keychron",
        model="K2",
        limit=3,
    )

    assert len(results) == 3
    assert all(item["category"] == "digital" for item in results)
    assert results[0]["brand"] == "Keychron"


def test_search_returns_empty_when_no_match(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    init_database()

    results = search_similar_items("digital", "unknown_device", None, None, limit=5)
    assert results == []


def test_search_supports_clothing_category(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    init_database()

    results = search_similar_items("clothing", "hoodie", "Uniqlo", None, limit=5)

    assert results
    assert all(item["category"] == "clothing" for item in results)


def test_search_supports_furniture_category(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    init_database()

    results = search_similar_items("furniture", "desk", "IKEA", None, limit=5)

    assert results
    assert all(item["category"] == "furniture" for item in results)


def test_search_supports_shoe_bag_category(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RESALE_AGENT_DB_PATH", str(tmp_path / "resale.db"))
    init_database()

    results = search_similar_items("shoe_bag", "sneakers", "Nike", None, limit=5)

    assert results
    assert all(item["category"] == "shoe_bag" for item in results)
