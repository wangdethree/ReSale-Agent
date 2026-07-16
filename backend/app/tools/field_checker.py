from __future__ import annotations

from typing import Any


REQUIRED_FIELDS: dict[str, list[str]] = {
    "digital": [
        "product_type",
        "brand",
        "model",
        "original_price",
        "purchase_date",
        "functional_status",
        "repair_history",
        "accessories",
        "additional_defects",
    ],
    "book": [
        "product_type",
        "model",
        "set_status",
        "notes_status",
        "damage_status",
        "original_price",
        "purchase_date",
    ],
    "appliance": [
        "product_type",
        "brand",
        "model",
        "original_price",
        "purchase_date",
        "functional_status",
        "repair_history",
        "accessories",
        "additional_defects",
        "delivery_options",
    ],
    "clothing": [
        "product_type",
        "brand",
        "model",
        "size",
        "material",
        "original_price",
        "purchase_date",
        "wear_status",
        "wash_status",
        "additional_defects",
        "delivery_options",
    ],
    "furniture": [
        "product_type",
        "brand",
        "model",
        "dimensions",
        "material",
        "original_price",
        "purchase_date",
        "functional_status",
        "installation_status",
        "additional_defects",
        "pickup_requirement",
        "delivery_options",
    ],
    "shoe_bag": [
        "product_type",
        "brand",
        "model",
        "size",
        "material",
        "original_price",
        "purchase_date",
        "wear_status",
        "clean_status",
        "authenticity_status",
        "accessories",
        "additional_defects",
        "delivery_options",
    ],
}


FIELD_QUESTIONS: dict[str, str] = {
    "product_type": "这件商品的具体类型是什么？例如机械键盘、Python 图书、桌面风扇、连帽卫衣、书桌、运动鞋或单肩包。",
    "brand": "商品品牌是什么？如果不确定，可以填写“不确定”。",
    "model": "商品型号、版本或 ISBN 是什么？如果不知道，可以填写“不确定”。",
    "original_price": "这件商品的原价大约是多少元？",
    "purchase_date": "大约是什么时候购买的？可以写 2024-05 或 2024 年。",
    "functional_status": "当前所有功能是否正常？请说明异常情况。",
    "repair_history": "是否维修、拆机、进水或更换过零件？",
    "accessories": "包装和配件是否齐全？请列出已有配件。",
    "additional_defects": "除了图片可见部分，还有其他瑕疵吗？没有可以填写“无”。",
    "set_status": "图书是否成套？如果是教材或套装，请说明缺不缺册。",
    "notes_status": "书内是否有笔记、划线或签名？",
    "damage_status": "是否有缺页、污损、开胶或明显破损？",
    "delivery_options": "支持邮寄还是自提？是否有原包装方便运输？",
    "size": "尺码是多少？例如 S、M、L、42 码或均码。",
    "material": "主要材质是什么？例如纯棉、羊毛、聚酯纤维、皮革。",
    "wear_status": "穿着频率和当前状态如何？例如穿过 3 次、轻微起球、无变形。",
    "wash_status": "是否已清洗或干洗？是否有缩水、掉色或染色情况？",
    "dimensions": "商品尺寸是多少？例如长宽高、座面高度或可折叠后的尺寸。",
    "installation_status": "当前是否已安装？是否方便拆装、是否缺少螺丝或配件？",
    "pickup_requirement": "搬运条件如何？例如是否仅自提、是否有电梯、是否需要买家自备搬运工具。",
    "clean_status": "当前清洁或保养状态如何？例如已清洁、鞋底已擦拭、皮面定期护理。",
    "authenticity_status": "购买渠道和真伪情况如何？例如专柜/官网购入、有小票或支持验货。",
}


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def find_missing_fields(category: str, product_data: dict[str, Any]) -> list[str]:
    required = REQUIRED_FIELDS.get(category, [])
    answers = product_data.get("user_answers") or {}
    missing: list[str] = []
    for field in required:
        direct_value = product_data.get(field)
        answer_value = answers.get(field)
        if not _has_value(direct_value) and not _has_value(answer_value):
            missing.append(field)
    return missing


def get_question_for_field(field: str) -> str:
    return FIELD_QUESTIONS.get(field, f"请补充 {field} 的信息。")
