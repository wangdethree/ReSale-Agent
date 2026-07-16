from __future__ import annotations

from typing import Any

from backend.app.repositories.product_repository import ProductRepository


def search_similar_items(
    category: str,
    product_type: str,
    brand: str | None,
    model: str | None,
    limit: int = 5,
    image_paths: list[str] | None = None,
    visual_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    """从本地 SQLite 模拟商品库查询相似商品。"""

    if not product_type:
        return []
    return ProductRepository().search_similar(
        category,
        product_type,
        brand,
        model,
        limit,
        image_paths=image_paths,
        visual_keywords=visual_keywords,
    )
