from __future__ import annotations

from typing import Any

import requests

from backend.app.services.listing_service import ListingService
from backend.app.services.negotiation_service import NegotiationService


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


def _state() -> dict[str, Any]:
    return {
        "category": "digital",
        "product_type": "mechanical_keyboard",
        "brand": "Keychron",
        "model": "K2",
        "visible_condition": "轻微使用痕迹",
        "visible_defects": ["空格键轻微划痕"],
        "additional_defects": ["背面有一处小划痕"],
        "original_price": 499,
        "purchase_date": "2024-05",
        "functional_status": "功能正常",
        "repair_history": "无维修",
        "accessories": ["原包装", "数据线"],
        "title": "闲置 Keychron K2 轻微使用痕迹",
        "suggested_floor_price": 246,
        "deal_price_min": 267,
    }


def test_listing_service_uses_text_model_without_hiding_defects(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": """
                            {
                              "title": "Keychron K2 机械键盘 自用闲置",
                              "description": "自用键盘，功能正常，配件齐全。",
                              "keywords": ["Keychron", "K2", "机械键盘"],
                              "photo_suggestions": ["补一张键帽细节图"]
                            }
                            """
                        }
                    }
                ]
            }
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_TEXT_MODEL", "text-model")
    monkeypatch.setattr(requests, "post", fake_post)

    listing = ListingService().generate(_state())

    assert listing["title"] == "Keychron K2 机械键盘 自用闲置"
    assert "空格键轻微划痕" in listing["description"]
    assert "背面有一处小划痕" in listing["description"]
    assert listing["defect_statement"].startswith("瑕疵说明")
    assert calls[0]["json"]["model"] == "text-model"


def test_negotiation_service_uses_text_model_when_price_is_safe(monkeypatch) -> None:
    def fake_post(_: str, **__: Any) -> FakeResponse:
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": """
                            {
                              "suggested_reply": "可以的，这个价格在可接受范围内，我们确认一下配件和交易方式。",
                              "next_strategy": "确认交易方式并推动成交。"
                            }
                            """
                        }
                    }
                ]
            }
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(requests, "post", fake_post)

    result = NegotiationService().handle(_state(), "270 可以吗", user_floor_price=246)

    assert result["below_floor_price"] is False
    assert result["suggested_reply"].startswith("可以的")
    assert result["next_strategy"] == "确认交易方式并推动成交。"


def test_negotiation_service_skips_text_model_below_floor_price(monkeypatch) -> None:
    calls: list[bool] = []

    def fake_post(*_: Any, **__: Any) -> FakeResponse:
        calls.append(True)
        return FakeResponse({"choices": []})

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(requests, "post", fake_post)

    result = NegotiationService().handle(_state(), "150 包邮行不行", user_floor_price=246)

    assert result["below_floor_price"] is True
    assert "最低接受价 246 元" in result["suggested_reply"]
    assert calls == []

