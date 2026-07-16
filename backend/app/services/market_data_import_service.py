from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from backend.app.core.exceptions import AppError
from backend.app.repositories.product_repository import ProductRepository


ALLOWED_CATEGORIES = {"digital", "book", "appliance", "clothing", "furniture", "shoe_bag"}
REQUIRED_COLUMNS = {"category", "product_type", "sold_price"}
OPTIONAL_COLUMNS = {
    "brand",
    "model",
    "condition_level",
    "age_months",
    "original_price",
    "listing_price",
    "accessories_complete",
    "description",
    "source_name",
    "source_url",
}
ACCEPTED_COLUMNS = sorted(REQUIRED_COLUMNS | OPTIONAL_COLUMNS)


class MarketDataImportService:
    def import_csv(self, content: bytes, source_name: str | None = None) -> dict[str, Any]:
        if not content.strip():
            raise AppError("CSV 文件不能为空")

        reader = csv.DictReader(StringIO(self._decode(content)))
        if not reader.fieldnames:
            raise AppError("CSV 需要包含表头")

        normalized_headers = {header.strip() for header in reader.fieldnames if header}
        missing = sorted(REQUIRED_COLUMNS - normalized_headers)
        if missing:
            raise AppError("CSV 缺少必填列：" + "、".join(missing))

        items: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        total_rows = 0
        fallback_source = (source_name or "").strip() or "用户导入 CSV"

        for row_number, raw_row in enumerate(reader, start=2):
            row = {
                str(key or "").strip(): str(value or "").strip()
                for key, value in raw_row.items()
            }
            if not any(row.values()):
                continue
            total_rows += 1
            try:
                items.append(self._parse_row(row, fallback_source))
            except ValueError as exc:
                errors.append({"row_number": row_number, "message": str(exc)})

        result = ProductRepository().import_reference_items(items) if items else {"imported_count": 0, "skipped_count": 0}
        return {
            "imported_count": result["imported_count"],
            "skipped_count": result["skipped_count"],
            "error_count": len(errors),
            "total_rows": total_rows,
            "source_name": fallback_source,
            "accepted_columns": ACCEPTED_COLUMNS,
            "errors": errors[:20],
        }

    def _decode(self, content: bytes) -> str:
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise AppError("CSV 仅支持 UTF-8 编码") from exc

    def _parse_row(self, row: dict[str, str], fallback_source: str) -> dict[str, Any]:
        category = row.get("category", "")
        if category not in ALLOWED_CATEGORIES:
            raise ValueError("category 不在支持范围内")

        product_type = row.get("product_type", "").strip()
        if not product_type:
            raise ValueError("product_type 不能为空")

        sold_price = self._positive_float(row.get("sold_price"), "sold_price")
        listing_price = self._optional_positive_float(row.get("listing_price"), "listing_price")
        if listing_price is None:
            listing_price = round(sold_price * 1.08, 2)
        original_price = self._optional_positive_float(row.get("original_price"), "original_price")
        if original_price is None:
            original_price = max(listing_price, sold_price)

        condition = row.get("condition_level") or "轻微使用痕迹"
        brand = row.get("brand") or None
        model = row.get("model") or None
        description = row.get("description") or self._default_description(brand, model, condition)

        return {
            "category": category,
            "product_type": product_type,
            "brand": brand,
            "model": model,
            "condition_level": condition,
            "age_months": self._non_negative_int(row.get("age_months") or "12", "age_months"),
            "original_price": round(original_price, 2),
            "listing_price": round(listing_price, 2),
            "sold_price": round(sold_price, 2),
            "accessories_complete": self._bool_value(row.get("accessories_complete")),
            "description": description,
            "source_name": row.get("source_name") or fallback_source,
            "source_type": "imported",
            "source_url": row.get("source_url") or None,
        }

    def _positive_float(self, value: str | None, field: str) -> float:
        parsed = self._optional_positive_float(value, field)
        if parsed is None or parsed <= 0:
            raise ValueError(f"{field} 必须大于 0")
        return parsed

    def _optional_positive_float(self, value: str | None, field: str) -> float | None:
        if value is None or not value.strip():
            return None
        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(f"{field} 必须是数字") from exc
        if parsed < 0:
            raise ValueError(f"{field} 不能小于 0")
        return parsed

    def _non_negative_int(self, value: str, field: str) -> int:
        try:
            parsed = int(float(value))
        except ValueError as exc:
            raise ValueError(f"{field} 必须是整数") from exc
        if parsed < 0:
            raise ValueError(f"{field} 不能小于 0")
        return parsed

    def _bool_value(self, value: str | None) -> bool:
        text = (value or "").strip().lower()
        if not text:
            return True
        return text in {"1", "true", "yes", "y", "是", "齐全", "完整"}

    def _default_description(self, brand: str | None, model: str | None, condition: str) -> str:
        product = " ".join(part for part in [brand, model] if part).strip() or "未命名商品"
        return f"{product}，{condition}，用户导入成交样本。"
