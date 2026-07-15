from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceItem:
    category: str
    product_type: str
    brand: str
    model: str
    condition_level: str
    age_months: int
    original_price: float
    listing_price: float
    sold_price: float
    accessories_complete: bool
    description: str

