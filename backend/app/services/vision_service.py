from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

import requests

from backend.app.core.config import get_settings
from backend.app.models.schemas import ProductConfirmation


class VisionService:
    """图片识别服务。

    V1 默认提供可解释的安全降级结果，保证没有模型密钥时仍能演示完整流程。
    后续接入真实多模态模型时，应保持 ProductConfirmation 的结构化输出。
    """

    def analyze_images(self, category: str, image_paths: list[str]) -> ProductConfirmation:
        settings = get_settings()
        if settings.openai_api_key:
            try:
                return self._analyze_with_model(category, image_paths, settings)
            except Exception:
                # 模型不可用时不阻塞主流程，让用户继续手动确认识别初稿。
                pass
        return self._fallback_analysis(category, image_paths)

    def _analyze_with_model(self, category: str, image_paths: list[str], settings: Any) -> ProductConfirmation:
        response = requests.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=self._build_request_payload(category, image_paths, settings.openai_vision_model),
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = self._parse_model_json(content)
        data["category"] = category
        return ProductConfirmation.model_validate(data)

    def _build_request_payload(self, category: str, image_paths: list[str], model: str) -> dict[str, Any]:
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "请识别这件二手商品，只返回 JSON。"
                    f"用户选择的类别是 {category}，只能在该类别范围内判断。"
                    "无法确定品牌、型号、颜色或瑕疵时返回 null 或空数组，不要编造。"
                ),
            }
        ]
        for path in image_paths:
            content.append({"type": "image_url", "image_url": {"url": self._image_to_data_url(path)}})

        return {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是二手商品图片识别助手。必须输出 JSON 对象，字段包括 "
                        "product_type, brand, model, color, visible_condition, "
                        "visible_defects, vision_confidence。"
                        "visible_condition 使用“接近全新/轻微使用痕迹/明显使用痕迹/存在明显瑕疵”之一。"
                        "vision_confidence 是 0 到 1 的数字。不要隐藏可见瑕疵。"
                    ),
                },
                {"role": "user", "content": content},
            ],
        }

    def _image_to_data_url(self, image_path: str) -> str:
        path = Path(image_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _parse_model_json(self, content: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(content, dict):
            return content
        text = content.strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("模型返回内容不是 JSON 对象")
        return parsed

    def _fallback_analysis(self, category: str, image_paths: list[str]) -> ProductConfirmation:
        filename_text = " ".join(Path(path).name.lower() for path in image_paths)
        base = {
            "category": category,
            "visible_condition": "轻微使用痕迹",
            "visible_defects": [],
            "vision_confidence": 0.52,
        }

        if category == "digital":
            base.update(self._infer_digital(filename_text))
        elif category == "book":
            base.update(self._infer_book(filename_text))
        elif category == "appliance":
            base.update(self._infer_appliance(filename_text))
        elif category == "clothing":
            base.update(self._infer_clothing(filename_text))

        return ProductConfirmation(**base)

    def _infer_digital(self, text: str) -> dict[str, object]:
        if "keychron" in text or "keyboard" in text or "k2" in text:
            return {
                "product_type": "mechanical_keyboard",
                "brand": "Keychron",
                "model": "K2",
                "color": "gray",
                "vision_confidence": 0.76,
                "visible_defects": ["按键和掌托区域可能存在轻微使用痕迹"],
            }
        if "airpods" in text:
            return {"product_type": "headphones", "brand": "Apple", "model": "AirPods Pro 2"}
        return {"product_type": "digital_device", "brand": None, "model": None}

    def _infer_book(self, text: str) -> dict[str, object]:
        if "python" in text:
            return {
                "product_type": "python_book_set",
                "brand": "人民邮电出版社",
                "model": "Python 编程：从入门到实践",
                "visible_defects": ["封面边角可能有轻微折痕"],
                "vision_confidence": 0.70,
            }
        return {"product_type": "book", "brand": None, "model": None}

    def _infer_appliance(self, text: str) -> dict[str, object]:
        if "fan" in text or "desk_fan" in text:
            return {
                "product_type": "desk_fan",
                "brand": "Midea",
                "model": "FT30-21M",
                "color": "white",
                "visible_defects": ["外壳可能有轻微划痕"],
                "vision_confidence": 0.72,
            }
        return {"product_type": "appliance", "brand": None, "model": None}

    def _infer_clothing(self, text: str) -> dict[str, object]:
        if "uniqlo" in text or "hoodie" in text or "卫衣" in text:
            return {
                "product_type": "hoodie",
                "brand": "Uniqlo",
                "model": "U 系列连帽卫衣",
                "color": "gray",
                "visible_defects": ["袖口或下摆可能有轻微使用痕迹"],
                "vision_confidence": 0.68,
            }
        if "nike" in text or "sneaker" in text or "shoe" in text:
            return {"product_type": "sneakers", "brand": "Nike", "model": "Air Force 1"}
        return {"product_type": "clothing", "brand": None, "model": None}
