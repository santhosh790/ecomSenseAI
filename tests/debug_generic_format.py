"""
Debug generic format to see row candidates
"""

from application.extraction_service import build_row_candidates
from application.vegetable_catalog_service import load_vegetable_catalog

# Generic format from user
generic_text = """jite name: LTRPM VEDAL

sINo Material description UOM Quantity) Delivery
4 |ONION BIG_UB_1X1KG KG 45 __| 25.07.2026
2_|POTATO LARGE_UB_1X1KG KG 20 | 25.07.2026
3__ [TOMATO COUNTRY_UB_1X1KG KG 30__| 25.07.2026
4 |CABBAGE_UB_1X1KG KG 6 __| 25.07.2026

[5 _ [LADIES FINGER_UB_1Xx1KG KG 5__| 25.07.2026
6 [GARLIC DRY_UB_4x1KG KG  4 __| 25.07.2026
7_|GINGER FRESH_UB_1X1KG KG 3__| 25.07.2026
8 [GREEN CHILLY_UB_1X1kG KG 2__| 25.07.2026
9 |BEETROOT_UB_1x1KG KG 65__| 25.07.2026
40 |CORIANDER LEAVES UB_1X1KG KG 1_| 25.07.2026
41 [BRINJAL VARI_UB_1X1kKG KG. 6 | 25.07.2026
12. |RAW MANGO_UB_1X1KG KG 10__| 25.07.2026
13 |CHOW CHOW_UB_1X1KG KG 35__| 25.07.2026
14 |RADISH WHITE_UB_1X1KG KG 20 | 25.07.2026
45 [CURRY LEAVES UB_1X1KG KG 1.5 | 25.07.2026
16 _|COCONUT FRESH_UB_1X1NOS EA 80__| 25.07.2026
47 [BEANS CLUSTER (GAWAR )_UB_1X1KG KG 12__| 25.07.2026"""

catalog = load_vegetable_catalog()
lines = [line.strip() for line in str(generic_text).splitlines() if line.strip()]

print("=" * 80)
print("RAW LINES DEBUG")
print("=" * 80)
for i, line in enumerate(lines, 1):
    print(f"{i:3}. {line}")

print("\n" + "=" * 80)
print("ROW CANDIDATES DEBUG")
print("=" * 80)

row_candidates = build_row_candidates(lines, catalog.noise_line_patterns)

for i, row in enumerate(row_candidates, 1):
    print(f"\n{i:3}. [{len(row):3} chars] {row}")

print("\n" + "=" * 80)
print(f"Total row candidates: {len(row_candidates)}")
print("=" * 80)
