"""Backward compatibility wrapper for infrastructure.product_catalog_repository."""
from infrastructure.product_catalog_repository import (
    ALIASES_FILE,
    DATA_DIR,
    PRODUCTS_FILE,
    VEGETABLES_FILE,
    ProductCatalog,
    VegetableCatalog,
    load_product_catalog,
    load_vegetable_catalog,
)

__all__ = [
    "ALIASES_FILE",
    "DATA_DIR",
    "PRODUCTS_FILE",
    "VEGETABLES_FILE",
    "ProductCatalog",
    "VegetableCatalog",
    "load_product_catalog",
    "load_vegetable_catalog",
]
