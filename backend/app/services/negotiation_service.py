from __future__ import annotations

import re
from typing import Any

from backend.app.services.text_model_service import TextModelService


class NegotiationService:
    def handle(self, state: dict[str, Any], buyer_message: str, user_floor_price: float | None = None) -> dict[str, Any]:
        offer_price = self._extract_offer_price(buyer_message)
        floor_price = float(
            user_floor_price
            or state.get("user_floor_price")
            or state.get("suggested_floor_price")
            or state.get("deal_price_min")
            or 0
        )
        intent = self._detect_intent(buyer_message, offer_price)
        below_floor = bool(offer_price is not None and floor_price and offer_price < floor_price)
        reply = self._build_reply(state, buyer_message, intent, offer_price, floor_price, below_floor)
        strategy = self._strategy(intent, below_floor)
        if not below_floor:
            try:
                model_result = self._reply_with_model(state, buyer_message, intent, offer_price, floor_price, reply, strategy)
            except Exception:
                model_result = None
            if model_result:
                reply = model_result["suggested_reply"]
                strategy = model_result["next_strategy"]
        return {
            "buyer_intent": intent,
            "offer_price": offer_price,
            "below_floor_price": below_floor,
            "suggested_reply": reply,
            "next_strategy": strategy,
        }

    def _extract_offer_price(self, message: str) -> float | None:
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:元|块|包邮)?", message)
        if not matches:
            return None
        return float(matches[0])

    def _detect_intent(self, message: str, offer_price: float | None) -> str:
        text = message.lower()
        if offer_price is not None or any(word in text for word in ["便宜", "刀", "砍", "包邮", "优惠"]):
            return "砍价"
        if any(word in text for word in ["瑕疵", "划痕", "成色", "新旧"]):
            return "询问成色"
        if any(word in text for word in ["邮寄", "自提", "运费", "哪里"]):
            return "询问交易方式"
        return "普通咨询"

    def _build_reply(
        self,
        state: dict[str, Any],
        buyer_message: str,
        intent: str,
        offer_price: float | None,
        floor_price: float,
        below_floor: bool,
    ) -> str:
        title = state.get("title") or state.get("model") or "这件商品"
        if intent == "砍价" and below_floor:
            return (
                f"感谢关注，{title} 目前功能和配件情况已经按描述说明。"
                f"您这个价格低于我的最低接受价 {floor_price:.0f} 元，暂时不太方便。"
                f"如果可以到 {max(floor_price, offer_price or 0):.0f} 元以上，我们可以继续沟通。"
            )
        if intent == "砍价" and offer_price is not None:
            return f"可以理解想优惠一点，{offer_price:.0f} 元这个价格我可以考虑，方便的话我们确认一下交易方式和配件细节。"
        if intent == "询问成色":
            return f"成色按描述属于 {state.get('visible_condition') or '轻微使用痕迹'}，已知瑕疵我也写在说明里了，可以再补细节图给你确认。"
        if intent == "询问交易方式":
            return f"交易方式可以沟通，{state.get('delivery_options') or '邮寄或自提都可以再确认'}。如果需要邮寄，我会尽量包装好。"
        return "感谢关注，有问题可以继续问我。商品信息、瑕疵和配件都按实际情况说明，价格也可以在合理范围内沟通。"

    def _strategy(self, intent: str, below_floor: bool) -> str:
        if below_floor:
            return "礼貌拒绝低价，给出最低可谈边界。"
        if intent == "砍价":
            return "确认买家诚意，保留小幅让价空间。"
        return "补充事实信息，推动买家确认交易方式。"

    def _reply_with_model(
        self,
        state: dict[str, Any],
        buyer_message: str,
        intent: str,
        offer_price: float | None,
        floor_price: float,
        fallback_reply: str,
        fallback_strategy: str,
    ) -> dict[str, str] | None:
        result = TextModelService().generate_json(
            system_prompt=(
                "你是二手商品议价回复助手。只返回 JSON，字段为 suggested_reply, next_strategy。"
                "回复必须礼貌、真实，必须基于商品信息和已知瑕疵。"
                f"不得建议低于最低接受价 {floor_price:.0f} 元成交。"
            ),
            payload={
                "buyer_message": buyer_message,
                "buyer_intent": intent,
                "offer_price": offer_price,
                "floor_price": floor_price,
                "title": state.get("title") or state.get("model") or state.get("product_type"),
                "visible_condition": state.get("visible_condition"),
                "visible_defects": state.get("visible_defects", []),
                "additional_defects": state.get("additional_defects", []),
                "delivery_options": state.get("delivery_options"),
                "template_reply": fallback_reply,
                "template_strategy": fallback_strategy,
            },
        )
        if not result:
            return None

        reply = str(result.get("suggested_reply") or "").strip()
        strategy = str(result.get("next_strategy") or "").strip()
        if not reply:
            return None

        return {
            "suggested_reply": reply,
            "next_strategy": strategy or fallback_strategy,
        }
