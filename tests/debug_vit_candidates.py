"""
Debug script to see what VIT candidates are being built.
"""

from application.extraction_service import (
    build_vit_row_candidates,
    extract_vit_row_fields,
    is_vit_document_text
)

# VIT PDF sample text - extracted from the attached PDF
vit_pdf_text = """Purchase Order
Vendor Code 405485
Vendor Name PKS FRESH
Vendor Address PKS FRESH, VELLORE, N0.19/1 SARATHY MANSION
Vendor Contact no
Vendor GST no
Vendor FSSAI no
Vendor Email id pksfresh1@gmail.com
PO Number 8110170328
PO Date 27.07.2026
PO Delivery date 28.07.2026
PO Type ZFPO
Purchase group CR1
Delivery address VELLORE INSTITUTE OF TECHNOLOGY, VIT Campus, Katpadi Taluk,, 1, VIT University Vellore,, Vellore, 632014
S.No Material Code Description HSN/SAC UOM Quantity Price per UOM SGST % CGST % IGST % GST Amount Total Net Amount
10 206607 ONION BIG_UB_1X1KG 07122000 KG 150.000 31.00 0 0 0 4,650
20 206610 POTATO LARGE_UB_1X1 KG 07122000 KG 100.000 20.00 0 0 0 2,000
30 206627 TOMATO COUNTRY_UB_1 X1KG 07122000 KG 175.000 21.00 0 0 0 3,675
"""

lines = [line.strip() for line in str(vit_pdf_text).splitlines() if line.strip()]

print("=" * 80)
print("VIT Document Detection:")
print("=" * 80)
is_vit = is_vit_document_text(vit_pdf_text)
print(f"Is VIT document: {is_vit}")

print("\n" + "=" * 80)
print("VIT Row Candidates:")
print("=" * 80)
candidates = build_vit_row_candidates(lines)
print(f"Found {len(candidates)} candidates\n")

for idx, candidate in enumerate(candidates, 1):
    print(f"\nCandidate {idx}:")
    print(f"  Raw: {candidate}")
    
    material, quantity = extract_vit_row_fields(candidate)
    print(f"  Material: {material}")
    print(f"  Quantity: {quantity}")
    
    if not quantity:
        print("  ⚠️  WARNING: No quantity extracted!")

print("\n" + "=" * 80)
