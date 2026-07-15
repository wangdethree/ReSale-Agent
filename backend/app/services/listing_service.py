from __future__ import annotations

from typing import Any


CATEGORY_LABELS = {
    "digital": "数码产品",
    "book": "图书",
    "appliance": "小家电",
}


class ListingService:
    def generate(self, state: dict[str, Any]) -> dict[str, Any]:
        category = state.get("category", "digital")
        product_type = state.get("product_type") or "闲置商品"
        brand = state.get("brand") or ""
        model = state.get("model") or ""
        condition = state.get("visible_condition") or "轻微使用痕迹"
        defects = [*state.get("visible_defects", []), *state.get("additional_defects", [])]
        defect_statement = self._defect_statement(defects)

        title_parts = ["闲置", brand, model or product_type, condition]
        title = " ".join(part for part in title_parts if part).strip()
        if len(title) > 60:
            title = title[:57] + "..."

        description = self._description(state, defect_statement)
        keywords = self._keywords(category, product_type, brand, model)
        photo_suggestions = self._photo_suggestions(category)

        return {
            "title": title,
            "description": description,
            "keywords": keywords,
            "defect_statement": defect_statement,
            "photo_suggestions": photo_suggestions,
        }

    def _description(self, state: dict[str, Any], defect_statement: str) -> str:
        brand_model = " ".join(
            part for part in [state.get("brand"), state.get("model") or state.get("product_type")] if part
        )
        lines = [
            f"出一件自用闲置 {brand_model or CATEGORY_LABELS.get(state.get('category'), '商品')}。",
            f"购买时间：{state.get('purchase_date') or '见补充说明'}，原价约 {state.get('original_price') or '未填写'} 元。",
            f"功能状态：{state.get('functional_status') or '已按实际情况填写'}。",
            f"维修记录：{state.get('repair_history') or '未发现维修记录'}。",
            f"配件情况：{self._join_list(state.get('accessories')) or '按现有配件出售'}。",
            defect_statement,
            "价格已参考本地模拟相似商品和规则折旧，欢迎合理沟通。",
        ]
        return "\n".join(lines)

    def _defect_statement(self, defects: list[str]) -> str:
        clean = [defect.strip() for defect in defects if str(defect).strip() and str(defect).strip() != "无"]
        if not clean:
            return "瑕疵说明：目前未补充明显瑕疵，建议买家下单前再确认细节图。"
        return "瑕疵说明：" + "；".join(clean) + "。"

    def _keywords(self, category: str, product_type: str, brand: str, model: str) -> list[str]:
        base = ["闲置", CATEGORY_LABELS.get(category, category), product_type]
        for value in [brand, model, "二手", "自用"]:
            if value:
                base.append(value)
        # 去重但保持顺序，方便前端直接展示。
        return list(dict.fromkeys(base))

    def _photo_suggestions(self, category: str) -> list[str]:
        common = ["补一张整体正面图", "补一张细节瑕疵特写", "补一张配件和包装合照"]
        if category == "digital":
            return [*common, "补一张通电或功能正常的展示图"]
        if category == "book":
            return [*common, "补一张目录页、笔记页或版本信息图"]
        return [*common, "补一张铭牌参数或通电状态图"]

    def _join_list(self, value: Any) -> str:
        if isinstance(value, list):
            return "、".join(str(item) for item in value if str(item).strip())
        return str(value or "")

