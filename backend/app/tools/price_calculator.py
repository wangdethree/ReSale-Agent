from __future__ import annotations

import re
from datetime import date
from statistics import median


DEPRECIATION_RANGES = [
    (3, 0.82),
    (12, 0.70),
    (24, 0.56),
    (10_000, 0.40),
]

CONDITION_FACTORS = {
    "接近全新": 1.10,
    "轻微使用痕迹": 1.00,
    "明显使用痕迹": 0.85,
    "存在明显瑕疵": 0.65,
}


def calculate_age_months(purchase_date: str | None, today: date | None = None) -> int:
    if not purchase_date:
        return 12

    today = today or date.today()
    numbers = [int(part) for part in re.findall(r"\d+", purchase_date)]
    if not numbers:
        return 12

    year = numbers[0]
    month = numbers[1] if len(numbers) > 1 and 1 <= numbers[1] <= 12 else 6
    if year < 100:
        year += 2000
    months = (today.year - year) * 12 + today.month - month
    return max(0, months)


def _depreciation_factor(age_months: int) -> float:
    for max_months, factor in DEPRECIATION_RANGES:
        if age_months <= max_months:
            return factor
    return 0.40


def normalize_condition(condition_level: str | None) -> str:
    value = (condition_level or "").lower()
    if any(token in value for token in ["全新", "new", "like_new", "接近"]):
        return "接近全新"
    if any(token in value for token in ["明显瑕疵", "defect", "故障", "破损"]):
        return "存在明显瑕疵"
    if any(token in value for token in ["明显", "heavy", "obvious"]):
        return "明显使用痕迹"
    return "轻微使用痕迹"


def _contains_positive_repair(repair_history: str | None) -> bool:
    value = (repair_history or "").strip().lower()
    if not value:
        return False
    negative_words = ["无", "没有", "未", "no", "none", "never"]
    return not any(word in value for word in negative_words)


def _functional_penalty(functional_status: str | None) -> float:
    value = (functional_status or "").lower()
    if not value:
        return 0.0
    if any(word in value for word in ["不正常", "故障", "坏", "无法", "不能", "broken"]):
        return 0.35
    if any(word in value for word in ["偶发", "轻微异常", "小问题"]):
        return 0.20
    return 0.0


def validate_price_result(result: dict[str, int | str | list[str]]) -> list[str]:
    errors: list[str] = []
    listing_price = int(result["listing_price"])
    deal_min = int(result["deal_price_min"])
    deal_max = int(result["deal_price_max"])
    floor_price = int(result["suggested_floor_price"])
    if min(listing_price, deal_min, deal_max, floor_price) < 0:
        errors.append("价格不能小于 0")
    if deal_min > deal_max:
        errors.append("成交区间下限不能高于上限")
    if listing_price < deal_max:
        errors.append("挂牌价不应低于成交区间上限")
    if floor_price > listing_price:
        errors.append("建议最低价不能高于挂牌价")
    return errors


def calculate_price_range(
    original_price: float,
    age_months: int,
    condition_level: str,
    functional_status: str,
    accessories_complete: bool,
    has_repair_history: bool,
    similar_prices: list[float],
) -> dict[str, int | str | list[str]]:
    """使用透明规则计算挂牌价、成交区间和建议最低价。"""

    original_price = max(float(original_price or 0), 0)
    normalized_condition = normalize_condition(condition_level)
    depreciation = _depreciation_factor(age_months)
    condition_factor = CONDITION_FACTORS[normalized_condition]
    adjustment = 1.0
    reasons = [
        f"原价按 {original_price:.0f} 元计算",
        f"使用约 {age_months} 个月，基础保值系数 {depreciation:.2f}",
        f"成色为“{normalized_condition}”，成色系数 {condition_factor:.2f}",
    ]

    if accessories_complete:
        adjustment += 0.05
        reasons.append("配件较完整，上调 5%")
    else:
        reasons.append("配件不完整或未确认，不做配件加成")

    if has_repair_history:
        adjustment -= 0.10
        reasons.append("存在维修或拆修记录，下调 10%")

    penalty = _functional_penalty(functional_status)
    if penalty:
        adjustment -= penalty
        reasons.append(f"功能状态存在风险，下调 {int(penalty * 100)}%")

    rule_price = original_price * depreciation * condition_factor * max(adjustment, 0.2)
    clean_similar_prices = [float(price) for price in similar_prices if price and price > 0]

    if len(clean_similar_prices) >= 3:
        market_price = median(clean_similar_prices)
        base_price = rule_price * 0.4 + market_price * 0.6
        confidence = "高" if len(clean_similar_prices) >= 5 else "中"
        reasons.append(f"融合 {len(clean_similar_prices)} 条模拟相似成交价，中位数 {market_price:.0f} 元")
    else:
        base_price = rule_price
        confidence = "低"
        reasons.append("相似商品样本不足，采用保守规则估价")

    listing_price = round(base_price * 1.12)
    deal_price_min = round(base_price * 0.95)
    deal_price_max = round(base_price * 1.05)
    suggested_floor_price = round(deal_price_min * 0.92)

    result: dict[str, int | str | list[str]] = {
        "listing_price": max(0, listing_price),
        "deal_price_min": max(0, deal_price_min),
        "deal_price_max": max(0, deal_price_max),
        "suggested_floor_price": max(0, suggested_floor_price),
        "price_confidence": confidence,
        "price_reasons": reasons,
    }

    errors = validate_price_result(result)
    if errors:
        raise ValueError("；".join(errors))
    return result


def parse_repair_history(repair_history: str | None) -> bool:
    return _contains_positive_repair(repair_history)

