from functools import lru_cache

from infrastructure.product_catalog_repository import load_product_catalog as load_product_catalog_from_repo


@lru_cache(maxsize=1)
def load_product_catalog():
    return load_product_catalog_from_repo()


# Backward-compatible alias
load_vegetable_catalog = load_product_catalog
