from __future__ import annotations

from pathlib import Path

from backend.app.models.schemas import ProductConfirmation


class VisionService:
    """图片识别服务。

    V1 默认提供可解释的安全降级结果，保证没有模型密钥时仍能演示完整流程。
    后续接入真实多模态模型时，应保持 ProductConfirmation 的结构化输出。
    """

    def analyze_images(self, category: str, image_paths: list[str]) -> ProductConfirmation:
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

