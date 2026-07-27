from functools import lru_cache

from infrastructure.vegetable_catalog_repository import load_vegetable_catalog as load_vegetable_catalog_from_repo


@lru_cache(maxsize=1)
def load_vegetable_catalog():
    return load_vegetable_catalog_from_repo()