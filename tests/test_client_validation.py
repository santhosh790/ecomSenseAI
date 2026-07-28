"""
Test both VIT and FVIT extraction to verify client-specific parsers.
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

# VIT format: 11-12 columns (Serial | ItemCode | Material | HSN UOM Qty | Rate | GST fields...)
vit_sample_text = """1
1010010
ONION
07031020 KG 150.000
25.00
0
0.00
9
2.25
27.25
4087.50
2
1010020
POTATO
07101000 KG 100.000
20.00
0
0.00
9
1.80
21.80
2180.00"""

# FVIT format: 8 columns (Serial | Material | HSN | UOM | Qty | Rate | GST% | Amount)
fvit_sample_text = """1
ONION_KG
070310
Kg
200
25.00
0%
5,000.00
2
POTATO_KG
071010
Kg
150
20.00
0%
3,000.00"""

catalog = load_vegetable_catalog()

print("=" * 80)
print("CLIENT-SPECIFIC PARSER VALIDATION")
print("=" * 80)

# Test VIT
print("\n1️⃣  Testing VIT (11-12 column format):")
print("-" * 80)
vit_results, vit_report = detect_vegetables(
    text=vit_sample_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    confidence_threshold=75,
    client_name="VIT"
)

print(f"Parser: {vit_report.get('parser_strategy', 'N/A')}")
print(f"Extracted: {len(vit_results)} items")
for item in vit_results:
    print(f"  ✓ {item['Source Name']:15} | {item['Quantity']:15}")

vit_success = len(vit_results) == 2 and all(item['Quantity'] for item in vit_results)
print(f"VIT Status: {'✅ PASS' if vit_success else '❌ FAIL'}")

# Test FVIT
print("\n2️⃣  Testing FVIT (8 column format):")
print("-" * 80)
fvit_results, fvit_report = detect_vegetables(
    text=fvit_sample_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    confidence_threshold=75,
    client_name="FVIT"
)

print(f"Parser: {fvit_report.get('parser_strategy', 'N/A')}")
print(f"Extracted: {len(fvit_results)} items")
for item in fvit_results:
    print(f"  ✓ {item['Source Name']:15} | {item['Quantity']:15}")

fvit_success = len(fvit_results) == 2 and all(item['Quantity'] for item in fvit_results)
print(f"FVIT Status: {'✅ PASS' if fvit_success else '❌ FAIL'}")

# Overall result
print("\n" + "=" * 80)
if vit_success and fvit_success:
    print("🎉 ALL CLIENTS VALIDATED: Both VIT and FVIT extraction working!")
else:
    print("⚠️  Some clients failed validation")
print("=" * 80)
