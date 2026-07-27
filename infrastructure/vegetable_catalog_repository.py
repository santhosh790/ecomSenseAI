import json
from pathlib import Path

from domain.models import VegetableCatalog


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VEGETABLES_FILE = DATA_DIR / "vegetables.json"
ALIASES_FILE = DATA_DIR / "aliases.json"


def _load_json(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def load_vegetable_catalog() -> VegetableCatalog:
    vegetables_payload = _load_json(VEGETABLES_FILE)
    aliases_payload = _load_json(ALIASES_FILE)

    return VegetableCatalog(
        vegetable_tamil_map=dict(vegetables_payload.get("vegetable_tamil_map", {})),
        vegetable_aliases=dict(aliases_payload),
        noise_line_patterns=list(vegetables_payload.get("noise_line_patterns", [])),
    )