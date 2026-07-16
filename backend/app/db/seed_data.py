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


def _clothing_items() -> list[ReferenceItem]:
    clothes = [
        ("hoodie", "Uniqlo", "U 系列连帽卫衣 M", 299),
        ("coat", "Zara", "羊毛混纺大衣 S", 899),
        ("sneakers", "Nike", "Air Force 1 42", 749),
        ("backpack", "Herschel", "Little America", 899),
        ("dress", "UR", "法式连衣裙 M", 399),
    ]
    conditions = [
        ("接近全新", 3, 0.62, True, "穿着次数少，版型保持较好。"),
        ("轻微使用痕迹", 10, 0.45, True, "正常穿着清洗，有轻微使用痕迹。"),
        ("明显使用痕迹", 20, 0.30, False, "局部有磨损或轻微起球，已如实说明。"),
    ]
    items: list[ReferenceItem] = []
    for product_type, brand, model, original in clothes:
        for condition, months, ratio, accessories, description in conditions:
            sold_price = round(original * ratio)
            items.append(
                ReferenceItem(
                    category="clothing",
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


def _furniture_items() -> list[ReferenceItem]:
    furniture = [
        ("desk", "IKEA", "Micke 米克书桌", 599),
        ("chair", "Hbada", "人体工学电脑椅", 899),
        ("shelf", "IKEA", "Kallax 卡莱克置物架", 499),
        ("coffee_table", "MUJI", "橡木茶几", 1290),
        ("nightstand", "NITORI", "简约床头柜", 399),
    ]
    conditions = [
        ("接近全新", 6, 0.58, True, "摆放使用时间短，结构稳固，表面干净。"),
        ("轻微使用痕迹", 18, 0.42, True, "日常使用，有轻微划痕或边角痕迹。"),
        ("明显使用痕迹", 36, 0.26, False, "表面磨损较明显，建议自提前看细节图。"),
    ]
    items: list[ReferenceItem] = []
    for product_type, brand, model, original in furniture:
        for condition, months, ratio, accessories, description in conditions:
            sold_price = round(original * ratio)
            items.append(
                ReferenceItem(
                    category="furniture",
                    product_type=product_type,
                    brand=brand,
                    model=model,
                    condition_level=condition,
                    age_months=months,
                    original_price=original,
                    listing_price=round(sold_price * 1.10),
                    sold_price=sold_price,
                    accessories_complete=accessories,
                    description=description,
                )
            )
    return items


def _shoe_bag_items() -> list[ReferenceItem]:
    products = [
        ("sneakers", "Nike", "Air Force 1 42", 749),
        ("running_shoes", "Adidas", "Ultraboost 22 41", 1299),
        ("leather_shoes", "Clarks", "Desert Boot 42", 1399),
        ("backpack", "Herschel", "Little America", 899),
        ("tote_bag", "Coach", "Field Tote 22", 2950),
        ("crossbody_bag", "Furla", "Metropolis Mini", 2680),
    ]
    conditions = [
        ("接近全新", 4, 0.66, True, "使用次数少，鞋底或包角磨损轻微。"),
        ("轻微使用痕迹", 12, 0.48, True, "正常使用，有轻微折痕、压痕或边角痕迹。"),
        ("明显使用痕迹", 24, 0.32, False, "鞋底、包角或五金磨损较明显，已如实说明。"),
    ]
    items: list[ReferenceItem] = []
    for product_type, brand, model, original in products:
        for condition, months, ratio, accessories, description in conditions:
            sold_price = round(original * ratio)
            items.append(
                ReferenceItem(
                    category="shoe_bag",
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
    return [
        *_digital_items(),
        *_book_items(),
        *_appliance_items(),
        *_clothing_items(),
        *_furniture_items(),
        *_shoe_bag_items(),
    ]
