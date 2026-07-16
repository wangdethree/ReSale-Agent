from __future__ import annotations

import re
from datetime import date
from statistics import median
from typing import Any


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


def _money(value: float) -> int:
    return max(0, round(value))


def _signed_money(value: float) -> int:
    return round(value)


def validate_price_result(result: dict[str, Any]) -> list[str]:
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
) -> dict[str, Any]:
    """使用透明规则计算挂牌价、成交区间和建议最低价。"""

    original_price = max(float(original_price or 0), 0)
    normalized_condition = normalize_condition(condition_level)
    depreciation = _depreciation_factor(age_months)
    condition_factor = CONDITION_FACTORS[normalized_condition]
    adjustment = 1.0
    accessories_adjustment = 0.0
    repair_adjustment = 0.0
    reasons = [
        f"原价按 {original_price:.0f} 元计算",
        f"使用约 {age_months} 个月，基础保值系数 {depreciation:.2f}",
        f"成色为“{normalized_condition}”，成色系数 {condition_factor:.2f}",
    ]

    if accessories_complete:
        accessories_adjustment = 0.05
        adjustment += accessories_adjustment
        reasons.append("配件较完整，上调 5%")
    else:
        reasons.append("配件不完整或未确认，不做配件加成")

    if has_repair_history:
        repair_adjustment = -0.10
        adjustment += repair_adjustment
        reasons.append("存在维修或拆修记录，下调 10%")

    penalty = _functional_penalty(functional_status)
    if penalty:
        adjustment -= penalty
        reasons.append(f"功能状态存在风险，下调 {int(penalty * 100)}%")

    final_adjustment = max(adjustment, 0.2)
    depreciation_price = original_price * depreciation
    condition_price = depreciation_price * condition_factor
    rule_price = original_price * depreciation * condition_factor * final_adjustment
    clean_similar_prices = [float(price) for price in similar_prices if price and price > 0]
    market_price: float | None = None
    rule_weight = 1.0
    market_weight = 0.0

    if len(clean_similar_prices) >= 3:
        market_price = median(clean_similar_prices)
        rule_weight = 0.4
        market_weight = 0.6
        base_price = rule_price * rule_weight + market_price * market_weight
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

    result: dict[str, Any] = {
        "listing_price": max(0, listing_price),
        "deal_price_min": max(0, deal_price_min),
        "deal_price_max": max(0, deal_price_max),
        "suggested_floor_price": max(0, suggested_floor_price),
        "price_confidence": confidence,
        "price_reasons": reasons,
        "price_breakdown": {
            "original_price": round(original_price, 2),
            "age_months": age_months,
            "depreciation_factor": depreciation,
            "normalized_condition": normalized_condition,
            "condition_factor": condition_factor,
            "accessories_adjustment": accessories_adjustment,
            "repair_adjustment": repair_adjustment,
            "functional_penalty": penalty,
            "final_adjustment": round(final_adjustment, 2),
            "rule_price": max(0, round(rule_price)),
            "market_sample_count": len(clean_similar_prices),
            "market_median_price": round(market_price, 2) if market_price is not None else None,
            "rule_weight": rule_weight,
            "market_weight": market_weight,
            "base_price": max(0, round(base_price)),
            "adjustment_steps": _build_adjustment_steps(
                original_price=original_price,
                depreciation=depreciation,
                depreciation_price=depreciation_price,
                normalized_condition=normalized_condition,
                condition_factor=condition_factor,
                condition_price=condition_price,
                accessories_adjustment=accessories_adjustment,
                repair_adjustment=repair_adjustment,
                functional_penalty=penalty,
                final_adjustment=final_adjustment,
                rule_price=rule_price,
                market_price=market_price,
                market_sample_count=len(clean_similar_prices),
                rule_weight=rule_weight,
                market_weight=market_weight,
                base_price=base_price,
                listing_price=listing_price,
                deal_price_min=deal_price_min,
                deal_price_max=deal_price_max,
                suggested_floor_price=suggested_floor_price,
            ),
        },
    }

    errors = validate_price_result(result)
    if errors:
        raise ValueError("；".join(errors))
    return result


def parse_repair_history(repair_history: str | None) -> bool:
    return _contains_positive_repair(repair_history)


def _build_adjustment_steps(
    *,
    original_price: float,
    depreciation: float,
    depreciation_price: float,
    normalized_condition: str,
    condition_factor: float,
    condition_price: float,
    accessories_adjustment: float,
    repair_adjustment: float,
    functional_penalty: float,
    final_adjustment: float,
    rule_price: float,
    market_price: float | None,
    market_sample_count: int,
    rule_weight: float,
    market_weight: float,
    base_price: float,
    listing_price: int,
    deal_price_min: int,
    deal_price_max: int,
    suggested_floor_price: int,
) -> list[dict[str, Any]]:
    adjustment_effect = condition_price * (final_adjustment - 1.0)
    steps = [
        {
            "label": "原价",
            "effect": 0,
            "amount": _money(original_price),
            "note": "用户填写或确认的购买原价",
        },
        {
            "label": "使用折旧",
            "effect": _signed_money(depreciation_price - original_price),
            "amount": _money(depreciation_price),
            "note": f"基础保值系数 {depreciation:.2f}",
        },
        {
            "label": "成色调整",
            "effect": _signed_money(condition_price - depreciation_price),
            "amount": _money(condition_price),
            "note": f"{normalized_condition}，成色系数 {condition_factor:.2f}",
        },
        {
            "label": "配件/维修/功能",
            "effect": _signed_money(adjustment_effect),
            "amount": _money(rule_price),
            "note": (
                f"配件 {accessories_adjustment:+.0%}，"
                f"维修 {repair_adjustment:+.0%}，"
                f"功能风险 {-functional_penalty:.0%}，最终调整 {final_adjustment:.2f}"
            ),
        },
        {
            "label": "规则估价",
            "effect": 0,
            "amount": _money(rule_price),
            "note": "由原价、折旧、成色和状态调整得到",
        },
        {
            "label": "市场融合",
            "effect": _signed_money(base_price - rule_price),
            "amount": _money(base_price),
            "note": (
                f"融合 {market_sample_count} 条本地模拟成交，中位数 {_money(market_price or 0)} 元，"
                f"规则权重 {rule_weight:.0%}，市场权重 {market_weight:.0%}"
                if market_price is not None
                else "相似样本不足，沿用规则估价"
            ),
        },
        {
            "label": "发布建议",
            "effect": _signed_money(listing_price - base_price),
            "amount": _money(listing_price),
            "note": f"成交区间 {deal_price_min}～{deal_price_max} 元，最低接受价 {suggested_floor_price} 元",
        },
    ]
    return steps
