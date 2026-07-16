from __future__ import annotations

from backend.app.tools.price_calculator import calculate_price_range, validate_price_result


def test_condition_worse_should_not_increase_price() -> None:
    better = calculate_price_range(
        original_price=499,
        age_months=8,
        condition_level="接近全新",
        functional_status="功能正常",
        accessories_complete=True,
        has_repair_history=False,
        similar_prices=[],
    )
    worse = calculate_price_range(
        original_price=499,
        age_months=8,
        condition_level="存在明显瑕疵",
        functional_status="功能正常",
        accessories_complete=True,
        has_repair_history=False,
        similar_prices=[],
    )
    assert better["listing_price"] > worse["listing_price"]


def test_repair_history_lowers_price() -> None:
    no_repair = calculate_price_range(
        original_price=499,
        age_months=10,
        condition_level="轻微使用痕迹",
        functional_status="功能正常",
        accessories_complete=True,
        has_repair_history=False,
        similar_prices=[],
    )
    repaired = calculate_price_range(
        original_price=499,
        age_months=10,
        condition_level="轻微使用痕迹",
        functional_status="功能正常",
        accessories_complete=True,
        has_repair_history=True,
        similar_prices=[],
    )
    assert repaired["listing_price"] < no_repair["listing_price"]


def test_similar_sample_shortage_sets_low_confidence_and_boundaries_are_valid() -> None:
    result = calculate_price_range(
        original_price=499,
        age_months=10,
        condition_level="轻微使用痕迹",
        functional_status="功能正常",
        accessories_complete=True,
        has_repair_history=False,
        similar_prices=[260, 270],
    )
    assert result["price_confidence"] == "低"
    assert validate_price_result(result) == []


def test_price_breakdown_explains_rule_and_market_weights() -> None:
    result = calculate_price_range(
        original_price=1000,
        age_months=8,
        condition_level="轻微使用痕迹",
        functional_status="功能正常",
        accessories_complete=True,
        has_repair_history=False,
        similar_prices=[500, 520, 540, 560, 580],
    )
    breakdown = result["price_breakdown"]

    assert breakdown["market_sample_count"] == 5
    assert breakdown["market_median_price"] == 540
    assert breakdown["rule_weight"] == 0.4
    assert breakdown["market_weight"] == 0.6
    assert breakdown["final_adjustment"] == 1.05
    assert breakdown["rule_price"] > 0
