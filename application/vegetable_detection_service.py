"""Backward compatibility wrapper for application.product_detection_service."""
from application.product_detection_service import (
    detect_products,
    detect_products_from_mapped_rows,
    detect_vegetables,
    detect_vegetables_from_mapped_rows,
    find_canonical_product_name,
    find_canonical_vegetable_name,
)

__all__ = [
    "detect_products",
    "detect_products_from_mapped_rows",
    "detect_vegetables",
    "detect_vegetables_from_mapped_rows",
    "find_canonical_product_name",
    "find_canonical_vegetable_name",
]
