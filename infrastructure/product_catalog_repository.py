import json
from dataclasses import dataclass
from pathlib import Path

try:
    from domain.models import ProductCatalog, VegetableCatalog
except ImportError:
    @dataclass(frozen=True)
    class ProductCatalog:
        product_tamil_map: dict[str, str]
        product_aliases: dict[str, str]
        noise_line_patterns: list[str]

        @property
        def vegetable_tamil_map(self) -> dict[str, str]:
            return self.product_tamil_map

        @property
        def vegetable_aliases(self) -> dict[str, str]:
            return self.product_aliases

    VegetableCatalog = ProductCatalog


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
VEGETABLES_FILE = DATA_DIR / "vegetables.json"
ALIASES_FILE = DATA_DIR / "aliases.json"


def _load_json(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def load_product_catalog() -> ProductCatalog:
    target_file = PRODUCTS_FILE if PRODUCTS_FILE.exists() else VEGETABLES_FILE
    products_payload = _load_json(target_file)
    aliases_payload = _load_json(ALIASES_FILE)

    mapping = products_payload.get("product_tamil_map") or products_payload.get("vegetable_tamil_map", {})

    return ProductCatalog(
        product_tamil_map=dict(mapping),
        product_aliases=dict(aliases_payload),
        noise_line_patterns=list(products_payload.get("noise_line_patterns", [])),
    )


# Backward-compatible alias
load_vegetable_catalog = load_product_catalog
