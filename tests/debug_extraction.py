"""
Debug extraction to see what's being matched
"""

from application.extraction_service import extract_row_fields, build_row_candidates
from application.vegetable_catalog_service import load_vegetable_catalog
import re

# Test specific rows
test_rows = [
    "4 |ONION BIG_UB_1X1KG KG 45 __| 25.07.2026",
    "2_|POTATO LARGE_UB_1X1KG KG 20 | 25.07.2026",
    "3__ [TOMATO COUNTRY_UB_1X1KG KG 30__| 25.07.2026",
    "7_|GINGER FRESH_UB_1X1KG KG 3__| 25.07.2026",
]

print("=" * 80)
print("EXTRACTION DEBUG")
print("=" * 80)

for row in test_rows:
    # Show compact version
    compact = re.sub(r"\s+", " ", str(row)).strip()
    material, quantity = extract_row_fields(row)
    
    print(f"\nOriginal: {row}")
    print(f"Compact:  {compact}")
    print(f"Result:   Material='{material}', Quantity='{quantity}'")
    
    if not quantity:
        print("  ❌ NO QUANTITY EXTRACTED")

print("\n" + "=" * 80)
