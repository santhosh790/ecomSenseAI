"""Backward compatibility wrapper for application.product_catalog_service."""
from application.product_catalog_service import (
    load_product_catalog,
    load_vegetable_catalog,
)

__all__ = [
    "load_product_catalog",
    "load_vegetable_catalog",
]
