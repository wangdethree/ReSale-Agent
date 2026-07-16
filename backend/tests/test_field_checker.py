from __future__ import annotations

from backend.app.tools.field_checker import find_missing_fields


def test_digital_required_fields_change_after_answer() -> None:
    state = {
        "category": "digital",
        "product_type": "mechanical_keyboard",
        "brand": "Keychron",
        "model": "K2",
    }
    missing = find_missing_fields("digital", state)
    assert "original_price" in missing
    assert "accessories" in missing

    state.update(
        {
            "original_price": 499,
            "purchase_date": "2024-05",
            "functional_status": "功能正常",
            "repair_history": "无维修",
            "accessories": ["原包装", "数据线"],
            "additional_defects": ["空格键轻微划痕"],
        }
    )
    assert find_missing_fields("digital", state) == []


def test_book_has_category_specific_required_fields() -> None:
    missing = find_missing_fields("book", {"category": "book", "product_type": "python_book_set"})
    assert "notes_status" in missing
    assert "repair_history" not in missing


def test_clothing_requires_size_and_wear_details() -> None:
    missing = find_missing_fields("clothing", {"category": "clothing", "product_type": "hoodie"})
    assert "size" in missing
    assert "wear_status" in missing
    assert "wash_status" in missing
    assert "repair_history" not in missing


def test_furniture_requires_dimensions_and_pickup_details() -> None:
    missing = find_missing_fields("furniture", {"category": "furniture", "product_type": "desk"})
    assert "dimensions" in missing
    assert "installation_status" in missing
    assert "pickup_requirement" in missing
    assert "wash_status" not in missing
