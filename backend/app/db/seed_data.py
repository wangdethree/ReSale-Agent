from __future__ import annotations

from backend.app.models.database import ReferenceItem


def _digital_items() -> list[ReferenceItem]:
    products = [
        ("mechanical_keyboard", "Keychron", "K2", 499),
        ("mechanical_keyboard", "Keychron", "K6", 529),
        ("mechanical_keyboard", "Logitech", "MX Mechanical", 999),
        ("headphones", "Sony", "WH-1000XM4", 2299),
        ("headphones", "Apple", "AirPods Pro 2", 1899),
        ("mouse", "Logitech", "MX Master 3S", 699),
        ("phone", "Apple", "iPhone 13", 5999),
        ("phone", "Xiaomi", "Mi 13", 3999),
        ("tablet", "Apple", "iPad Air 5", 4399),
        ("camera", "DJI", "Osmo Pocket 3", 3499),
    ]
    conditions = [
        ("接近全新", 3, 0.78, True, "外观干净，配件齐全。"),
        ("轻微使用痕迹", 9, 0.62, True, "日常使用，功能正常，有轻微痕迹。"),
        ("明显使用痕迹", 18, 0.48, False, "外观有明显磨损，核心功能正常。"),
    ]
    items: list[ReferenceItem] = []
    for product_type, brand, model, original in products:
        for condition, months, ratio, accessories, description in conditions:
            sold_price = round(original * ratio)
            items.append(
                ReferenceItem(
                    category="digital",
                    product_type=product_type,
                    brand=brand,
                    model=model,
                    condition_level=condition,
                    age_months=months,
                    original_price=original,
                    listing_price=round(sold_price * 1.12),
                    sold_price=sold_price,
                    accessories_complete=accessories,
                    description=description,
                )
            )
    return items


def _book_items() -> list[ReferenceItem]:
    books = [
        ("python_book_set", "人民邮电出版社", "Python 编程：从入门到实践 第3版", 159),
        ("python_book_set", "机械工业出版社", "流畅的 Python 第2版", 199),
        ("textbook", "高等教育出版社", "线性代数 第六版", 49),
        ("textbook", "清华大学出版社", "数据结构 C语言版", 59),
        ("novel", "上海译文出版社", "百年孤独 精装版", 55),
    ]
    conditions = [
        ("轻微使用痕迹", 8, 0.58, True, "少量翻阅痕迹，页面完整。"),
        ("明显使用痕迹", 16, 0.42, True, "有少量笔记，不影响阅读。"),
        ("存在明显瑕疵", 28, 0.28, False, "封面有折痕，内页无缺页。"),
    ]
    items: list[ReferenceItem] = []
    for product_type, brand, model, original in books:
        for condition, months, ratio, accessories, description in conditions:
            sold_price = round(original * ratio)
            items.append(
                ReferenceItem(
                    category="book",
                    product_type=product_type,
                    brand=brand,
                    model=model,
                    condition_level=condition,
                    age_months=months,
                    original_price=original,
                    listing_price=round(sold_price * 1.15),
                    sold_price=sold_price,
                    accessories_complete=accessories,
                    description=description,
                )
            )
    return items


def _appliance_items() -> list[ReferenceItem]:
    appliances = [
        ("desk_fan", "Midea", "FT30-21M", 169),
        ("desk_lamp", "Yeelight", "V1 Pro", 399),
        ("hair_dryer", "Panasonic", "EH-NA46", 499),
        ("kettle", "Midea", "MK-SH15", 129),
        ("air_fryer", "Joyoung", "KL35", 399),
    ]
    conditions = [
        ("接近全新", 4, 0.68, True, "使用次数少，功能正常。"),
        ("轻微使用痕迹", 14, 0.50, True, "有轻微划痕，功能正常。"),
        ("明显使用痕迹", 30, 0.34, False, "外观磨损较明显，仍可正常使用。"),
    ]
    items: list[ReferenceItem] = []
    for product_type, brand, model, original in appliances:
        for condition, months, ratio, accessories, description in conditions:
            sold_price = round(original * ratio)
            items.append(
                ReferenceItem(
                    category="appliance",
                    product_type=product_type,
                    brand=brand,
                    model=model,
                    condition_level=condition,
                    age_months=months,
                    original_price=original,
                    listing_price=round(sold_price * 1.12),
                    sold_price=sold_price,
                    accessories_complete=accessories,
                    description=description,
                )
            )
    return items


def get_seed_items() -> list[ReferenceItem]:
    return [*_digital_items(), *_book_items(), *_appliance_items()]

