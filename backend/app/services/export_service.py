from __future__ import annotations

from typing import Any


class ExportService:
    def build_markdown(self, state: dict[str, Any]) -> str:
        similar_lines = [
            f"- {item.get('brand', '')} {item.get('model', '')}：模拟成交价 {item.get('sold_price')} 元，{item.get('description')}"
            for item in state.get("similar_items", [])
        ]
        reason_lines = [f"- {reason}" for reason in state.get("price_reasons", [])]
        photo_lines = [f"- {item}" for item in state.get("photo_suggestions", [])]
        keyword_text = "、".join(state.get("keywords", []))

        return "\n".join(
            [
                f"# {state.get('title') or '出售方案'}",
                "",
                "## 估价建议",
                f"- 建议挂牌价：{state.get('listing_price', '未生成')} 元",
                f"- 合理成交区间：{state.get('deal_price_min', '未生成')}～{state.get('deal_price_max', '未生成')} 元",
                f"- 建议最低接受价：{state.get('suggested_floor_price', '未生成')} 元",
                f"- 估价置信度：{state.get('price_confidence', '未生成')}",
                "",
                "## 估价依据",
                *(reason_lines or ["- 暂无估价依据"]),
                "",
                "## 相似商品",
                *(similar_lines or ["- 未找到足够相似商品，当前结果仅为规则估价。"]),
                "",
                "## 出售文案",
                state.get("description") or "尚未生成文案。",
                "",
                "## 搜索关键词",
                keyword_text or "暂无关键词",
                "",
                "## 瑕疵声明",
                state.get("defect_statement") or "暂无瑕疵声明。",
                "",
                "## 拍照建议",
                *(photo_lines or ["- 补充清晰照片后再发布。"]),
            ]
        )

