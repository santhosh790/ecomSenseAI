"""
Debug script to test with REAL PDF extraction format.
"""

from application.extraction_service import (
    build_vit_row_candidates,
    extract_vit_row_fields,
    is_vit_document_text,
    detect_vegetables
)
from application.vegetable_catalog_service import load_vegetable_catalog

# REAL PDF extraction - each field on separate line!
real_pdf_text = """Purchase Order
Vendor Code
405485
Vendor Name
PKS FRESH
S.N
o
Material
Code
Description
HSN/SAC UO
M
Quantity
Price per
UOM
10
206607
ONION
BIG_UB_1X1KG
07122000 KG 150.000
31.00
0
0
0 
4,650 
20
206610
POTATO
LARGE_UB_1X1
KG
07122000 KG 100.000
20.00
0
0
0 
2,000 
30
206627
TOMATO
COUNTRY_UB_1
X1KG
07122000 KG 175.000
21.00
"""

catalog = load_vegetable_catalog()

print("=" * 80)
print("Testing with REAL PDF extraction format (multi-line)")
print("=" * 80)

lines = [line.strip() for line in str(real_pdf_text).splitlines() if line.strip()]
print(f"\nTotal lines: {len(lines)}")
print("\nFirst 30 lines:")
for i, line in enumerate(lines[:30], 1):
    print(f"{i:3}. {line}")

print("\n" + "=" * 80)
print("VIT Candidate Building:")
print("=" * 80)
candidates = build_vit_row_candidates(lines)
print(f"Found {len(candidates)} candidates")

for idx, candidate in enumerate(candidates, 1):
    print(f"\n{idx}. {candidate}")
    material, qty = extract_vit_row_fields(candidate)
    print(f"   Material: {material}, Qty: {qty}")

print("\n" + "=" * 80)
print("Full Detection Test:")
print("=" * 80)

results, report = detect_vegetables(
    text=real_pdf_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    client_name="VIT"
)

print(f"\nExtracted {len(results)} items:")
for item in results:
    print(f"  {item['Source Name']:20} | {item['Quantity']:15} | Conf: {item['Confidence']}%")
