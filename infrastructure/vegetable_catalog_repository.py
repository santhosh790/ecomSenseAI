import json
from dataclasses import dataclass
from pathlib import Path

try:
    from domain.models import VegetableCatalog
except ImportError:
    @dataclass(frozen=True)
    class VegetableCatalog:
        vegetable_tamil_map: dict[str, str]
        vegetable_aliases: dict[str, str]
        noise_line_patterns: list[str]


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