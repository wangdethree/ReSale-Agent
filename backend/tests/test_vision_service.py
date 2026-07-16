from __future__ import annotations

from typing import Any

import requests

from backend.app.services.vision_service import VisionService


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


def test_vision_service_uses_openai_compatible_model(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "keyboard.jpg"
    image_path.write_bytes(b"fake image bytes")
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
                              "product_type": "mechanical_keyboard",
                              "brand": "Keychron",
                              "model": "K2",
                              "color": "gray",
                              "visible_condition": "轻微使用痕迹",
                              "visible_defects": ["空格键轻微划痕"],
                              "vision_confidence": 0.88
                            }
                            """
                        }
                    }
                ]
            }
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setattr(requests, "post", fake_post)

    result = VisionService().analyze_images("digital", [str(image_path)])

    assert result.brand == "Keychron"
    assert result.model == "K2"
    assert result.vision_confidence == 0.88
    assert calls[0]["url"] == "https://example.test/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0]["json"]["response_format"] == {"type": "json_object"}


def test_vision_service_falls_back_when_model_fails(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "keychron_k2.jpg"
    image_path.write_bytes(b"fake image bytes")

    def fake_post(*_: Any, **__: Any) -> None:
        raise requests.Timeout("timeout")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(requests, "post", fake_post)

    result = VisionService().analyze_images("digital", [str(image_path)])

    assert result.brand == "Keychron"
    assert result.model == "K2"
    assert result.vision_confidence == 0.76


def test_vision_service_furniture_fallback(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "ikea_desk.jpg"
    image_path.write_bytes(b"fake image bytes")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = VisionService().analyze_images("furniture", [str(image_path)])

    assert result.brand == "IKEA"
    assert result.product_type == "desk"
    assert result.visible_defects
