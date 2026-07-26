import ast
import json
import re
from pathlib import Path

import fitz
from PIL import Image, ImageOps, ImageFilter
import pytesseract

APP_FILE = Path("ecomSenseAI.py")
DATA_DIR = Path("data")
OUT_FILE = Path("batch_results.json")

code = APP_FILE.read_text(encoding="utf-8")
module = ast.parse(code)

wanted_assigns = {
    "VEGETABLE_TAMIL_MAP",
    "VEGETABLE_ALIASES",
    "NOISE_LINE_PATTERNS",
}
wanted_funcs = {
    "normalize_text",
    "normalize_material_name",
    "is_noise_line",
    "extract_row_quantity",
    "extract_row_fields",
    "build_row_candidates",
    "find_canonical_vegetable_name",
    "is_candidate_line",
    "build_extraction_report",
    "detect_vegetables",
}

snippets = []
for node in module.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted_assigns:
                snippets.append(ast.get_source_segment(code, node))
                break
    elif isinstance(node, ast.FunctionDef) and node.name in wanted_funcs:
        snippets.append(ast.get_source_segment(code, node))

ns = {"re": re}
exec("\n\n".join(snippets), ns)
detect_vegetables = ns["detect_vegetables"]


def read_pdf_text(path: Path) -> str:
    text_parts = []
    doc = fitz.open(path)
    for page in doc:
        text_parts.append(page.get_text())
    return "\n".join(text_parts)


def read_image_text(path: Path) -> str:
    image = Image.open(path)
    gray = ImageOps.grayscale(image)
    enhanced = ImageOps.autocontrast(gray)
    sharpened = enhanced.filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(sharpened)


results = []
for file_path in sorted(DATA_DIR.glob("*")):
    if not file_path.is_file():
        continue

    ext = file_path.suffix.lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        continue

    if ext == ".pdf":
        raw_text = read_pdf_text(file_path)
    else:
        raw_text = read_image_text(file_path)

    items, report = detect_vegetables(raw_text, return_details=True)

    unique_names = sorted(
        {
            item.get("Source Name", "")
            for item in items
            if item.get("Source Name")
        }
    )

    results.append(
        {
            "file": str(file_path),
            "kind": ext,
            "chars": len(raw_text),
            "extracted_rows": len(items),
            "with_quantity": report.get("with_quantity", 0),
            "candidate_rows": report.get("candidate_lines", 0),
            "high_confidence": report.get("high_confidence", 0),
            "unmatched_candidate_rows": len(report.get("unmatched_lines", [])),
            "first_10_veg": unique_names[:10],
            "sample_rows": items[:5],
        }
    )

OUT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(f"written:{OUT_FILE}")
