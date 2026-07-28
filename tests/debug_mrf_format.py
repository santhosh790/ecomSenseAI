"""
Debug MRF format row candidates
"""

from application.extraction_service import build_row_candidates, extract_row_fields
from application.vegetable_catalog_service import load_vegetable_catalog
import re

mrf_text = """SITE [> MRF ARAKKONAM =| vom[>| 27-30
206564 |BRINJAL VARI_UB_1X1KG KG 50
206569 |[CABBAGE_UB_1X1KG Ko | 150
206573 |CARROT_UB_1X1KG KG 50
206578 [COCONUT FRESH_UB_1X1NOS|_EA 300
206579 [CORIANDER LEAVES_UB_1X1K|_KG 8
206583 [CURRY LEAVES_UB_1X1KG KG 8
206392 [GARLIC DRY_UB_1X1KG Broke|__KG 8
206586 |GINGER FRESH_UB_1X1KG KG 15
206589 [GREEN CHILLY_UB_1X1KG KG 2
206598 [LADIES FINGER_UB_1X1KG KG 65
206607 |ONION BIG_UB_1X1KG Ke | 250
206610 | POTATO LARGE_UB_1X1KG Ke | 250
206611 [RADISH WHITE_UB_1X1KG KG 50
206627 |TOMATO COUNTRY_UB_1X1Kq KG | 250"""

catalog = load_vegetable_catalog()
lines = [line.strip() for line in str(mrf_text).splitlines() if line.strip()]

print("=" * 80)
print("MRF FORMAT ROW CANDIDATES")
print("=" * 80)

row_candidates = build_row_candidates(lines, catalog.noise_line_patterns)

for i, row in enumerate(row_candidates, 1):
    material, quantity = extract_row_fields(row)
    compact = re.sub(r"\s+", " ", str(row)).strip()
    
    status = "✓" if quantity else "✗"
    print(f"\n{i:2}. {status} Row: {row}")
    print(f"      Compact: {compact}")
    print(f"      Result: Material='{material}', Quantity='{quantity}'")

print("\n" + "=" * 80)
print(f"Total candidates: {len(row_candidates)}")
print("=" * 80)
