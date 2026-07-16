from __future__ import annotations

from typing import Any

from backend.app.services.text_model_service import TextModelService


CATEGORY_LABELS = {
    "digital": "数码产品",
    "book": "图书",
    "appliance": "小家电",
    "clothing": "服装",
    "furniture": "家具",
    "shoe_bag": "鞋包",
}

PLATFORM_LABELS = {
    "xianyu": "闲鱼",
    "zhuanzhuan": "转转",
    "xiaohongshu": "小红书",
}


class ListingService:
    def generate(self, state: dict[str, Any]) -> dict[str, Any]:
        template = self._template_listing(state)
        try:
            model_listing = self._generate_with_model(state, template)
        except Exception:
            model_listing = None
        listing = model_listing or template
        listing["platform_copies"] = self._platform_copies(state, listing)
        return listing

    def _template_listing(self, state: dict[str, Any]) -> dict[str, Any]:
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
            "platform_copies": [],
        }

    def _generate_with_model(self, state: dict[str, Any], template: dict[str, Any]) -> dict[str, Any] | None:
        payload = {
            "category": state.get("category"),
            "product_type": state.get("product_type"),
            "brand": state.get("brand"),
            "model": state.get("model"),
            "color": state.get("color"),
            "visible_condition": state.get("visible_condition"),
            "visible_defects": state.get("visible_defects", []),
            "additional_defects": state.get("additional_defects", []),
            "purchase_date": state.get("purchase_date"),
            "original_price": state.get("original_price"),
            "functional_status": state.get("functional_status"),
            "repair_history": state.get("repair_history"),
            "accessories": state.get("accessories", []),
            "delivery_options": state.get("delivery_options"),
            "size": state.get("size"),
            "material": state.get("material"),
            "wear_status": state.get("wear_status"),
            "wash_status": state.get("wash_status"),
            "dimensions": state.get("dimensions"),
            "installation_status": state.get("installation_status"),
            "pickup_requirement": state.get("pickup_requirement"),
            "clean_status": state.get("clean_status"),
            "authenticity_status": state.get("authenticity_status"),
            "template": template,
        }
        result = TextModelService().generate_json(
            system_prompt=(
                "你是二手商品发布文案助手。只返回 JSON，字段为 title, description, "
                "keywords, photo_suggestions。不要输出价格，不要使用绝对全新、完美无瑕等无法验证表述，"
                "不得隐藏用户已确认的瑕疵。"
            ),
            payload=payload,
        )
        if not result:
            return None

        title = str(result.get("title") or template["title"]).strip()[:60]
        description = str(result.get("description") or template["description"]).strip()
        defect_statement = template["defect_statement"]
        if defect_statement not in description:
            description = f"{description}\n{defect_statement}"

        keywords = self._coerce_str_list(result.get("keywords")) or template["keywords"]
        photo_suggestions = self._coerce_str_list(result.get("photo_suggestions")) or template["photo_suggestions"]

        return {
            "title": title or template["title"],
            "description": description or template["description"],
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
            *self._condition_lines(state),
            defect_statement,
            "价格已参考本地模拟相似商品和规则折旧，欢迎合理沟通。",
        ]
        return "\n".join(lines)

    def _condition_lines(self, state: dict[str, Any]) -> list[str]:
        if state.get("category") == "clothing":
            return [
                f"尺码/材质：{state.get('size') or '未填写'}，{state.get('material') or '未填写'}。",
                f"穿着清洗：{state.get('wear_status') or '已按实际情况填写'}；{state.get('wash_status') or '未补充'}。",
            ]
        if state.get("category") == "furniture":
            return [
                f"尺寸/材质：{state.get('dimensions') or '未填写'}，{state.get('material') or '未填写'}。",
                f"结构状态：{state.get('functional_status') or '已按实际情况填写'}；{state.get('installation_status') or '安装状态未补充'}。",
                f"搬运条件：{state.get('pickup_requirement') or '待沟通'}。",
            ]
        if state.get("category") == "shoe_bag":
            return [
                f"尺码/材质：{state.get('size') or '未填写'}，{state.get('material') or '未填写'}。",
                f"使用清洁：{state.get('wear_status') or '已按实际情况填写'}；{state.get('clean_status') or '清洁状态未补充'}。",
                f"渠道验货：{state.get('authenticity_status') or '购买渠道和验货情况待补充'}。",
            ]
        return [
            f"功能状态：{state.get('functional_status') or '已按实际情况填写'}。",
            f"维修记录：{state.get('repair_history') or '未发现维修记录'}。",
            f"配件情况：{self._join_list(state.get('accessories')) or '按现有配件出售'}。",
        ]

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
        if category == "clothing":
            return [*common, "补一张尺码标、面料标和上身/平铺效果图"]
        if category == "furniture":
            return [*common, "补一张尺寸参照图、边角瑕疵图和拆装连接处细节图"]
        if category == "shoe_bag":
            return [*common, "补一张鞋底/包角磨损图、尺码标和购买凭证或防伪细节图"]
        return [*common, "补一张铭牌参数或通电状态图"]

    def _platform_copies(self, state: dict[str, Any], listing: dict[str, Any]) -> list[dict[str, Any]]:
        title = listing["title"]
        keywords = listing.get("keywords", [])
        defect_statement = listing.get("defect_statement") or self._defect_statement([])
        price = state.get("listing_price")
        deal_min = state.get("deal_price_min")
        deal_max = state.get("deal_price_max")
        price_text = f"建议挂 {price} 元" if price is not None else "价格可合理沟通"
        deal_text = f"参考成交区间 {deal_min}～{deal_max} 元" if deal_min and deal_max else "价格已按当前信息估算"
        delivery = state.get("delivery_options") or "支持当面或邮寄，具体可沟通"
        product = self._product_name(state)
        accessories = self._join_list(state.get("accessories")) or "按现有配件出售"
        status_label, status_value = self._status_label_and_value(state)
        detail_label, detail_value = self._detail_label_and_value(state, accessories)

        return [
            {
                "platform": "xianyu",
                "platform_label": PLATFORM_LABELS["xianyu"],
                "title": title,
                "body": "\n".join(
                    [
                        f"自用闲置 {product} 出手，{price_text}。",
                        f"成色：{state.get('visible_condition') or '轻微使用痕迹'}，{status_label}：{status_value}。",
                        f"{detail_label}：{detail_value}。",
                        defect_statement,
                        f"{deal_text}，接受合理沟通，低价离谱就不接了。",
                        f"交易方式：{delivery}。",
                    ]
                ),
                "tags": self._platform_tags(keywords, ["自用闲置", "可小刀"]),
            },
            {
                "platform": "zhuanzhuan",
                "platform_label": PLATFORM_LABELS["zhuanzhuan"],
                "title": f"{product}｜已验信息清楚",
                "body": "\n".join(
                    [
                        f"商品：{product}",
                        f"建议价格：{price_text}，{deal_text}",
                        f"购买时间：{state.get('purchase_date') or '见补充说明'}",
                        f"{status_label}：{status_value}",
                        f"{detail_label}：{detail_value}",
                        defect_statement,
                        "适合想要信息透明、快速确认细节的买家。",
                    ]
                ),
                "tags": self._platform_tags(keywords, ["验机友好", "信息透明"]),
            },
            {
                "platform": "xiaohongshu",
                "platform_label": PLATFORM_LABELS["xiaohongshu"],
                "title": f"闲置分享｜{product}",
                "body": "\n".join(
                    [
                        f"整理闲置时翻到 {product}，准备转给更需要的人。",
                        f"我会比较在意把信息说清楚：{deal_text}，当前{price_text}。",
                        f"实际状态是 {state.get('visible_condition') or '轻微使用痕迹'}，{status_value}。",
                        f"{defect_statement}",
                        f"{detail_label}：{detail_value}。感兴趣可以先看细节图再决定。",
                    ]
                ),
                "tags": self._platform_tags(keywords, ["闲置转让", "好物循环"]),
            },
        ]

    def _product_name(self, state: dict[str, Any]) -> str:
        parts = [state.get("brand"), state.get("model") or state.get("product_type")]
        product = " ".join(str(part).strip() for part in parts if str(part or "").strip())
        return product or CATEGORY_LABELS.get(state.get("category"), "闲置商品")

    def _status_label_and_value(self, state: dict[str, Any]) -> tuple[str, str]:
        if state.get("category") == "clothing":
            return "穿着状态", str(state.get("wear_status") or "按实际情况说明")
        if state.get("category") == "shoe_bag":
            return "使用状态", str(state.get("wear_status") or "按实际情况说明")
        if state.get("category") == "furniture":
            return "结构状态", str(state.get("functional_status") or "按实际情况说明")
        return "功能", str(state.get("functional_status") or "按实际情况说明")

    def _detail_label_and_value(self, state: dict[str, Any], accessories: str) -> tuple[str, str]:
        if state.get("category") == "clothing":
            return "尺码/材质", f"{state.get('size') or '未填写'}，{state.get('material') or '未填写'}"
        if state.get("category") == "shoe_bag":
            authenticity = state.get("authenticity_status") or "购买渠道和验货情况待补充"
            return "尺码/验货", f"{state.get('size') or '未填写'}，{authenticity}"
        if state.get("category") == "furniture":
            pickup = state.get("pickup_requirement") or state.get("delivery_options") or "搬运方式待沟通"
            return "尺寸/搬运", f"{state.get('dimensions') or '未填写'}，{pickup}"
        return "配件", accessories

    def _platform_tags(self, keywords: list[str], extra: list[str]) -> list[str]:
        return list(dict.fromkeys([*keywords, *extra]))[:8]

    def _join_list(self, value: Any) -> str:
        if isinstance(value, list):
            return "、".join(str(item) for item in value if str(item).strip())
        return str(value or "")

    def _coerce_str_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]
