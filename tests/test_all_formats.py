"""
Comprehensive test for all supported formats
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

catalog = load_vegetable_catalog()

# Test formats
test_cases = [
    ("VIT (11-12 column)", "VIT", """1
1010010
ONION
07031020 KG 150.000
25.00""", 1, 1),
    
    ("FVIT (8 column)", "FVIT", """1
ONION_KG
070310
Kg
200
25.00""", 1, 1),
    
    ("Generic (with decorations)", None, """4 |ONION BIG_UB_1X1KG KG 45 __| 25.07.2026
2_|POTATO LARGE_UB_1X1KG KG 20 | 25.07.2026""", 2, 2),
    
    ("MRF (with OCR errors)", None, """206564 |BRINJAL VARI_UB_1X1KG KG 50
206569 |[CABBAGE_UB_1X1KG Ko | 150
206578 [COCONUT FRESH_UB_1X1NOS|_EA 300
206607 |ONION BIG_UB_1X1KG Ke | 250""", 4, 4),
]

print("=" * 80)
print("COMPREHENSIVE FORMAT VALIDATION")
print("=" * 80)

all_passed = True

for format_name, client_name, text, expected_items, expected_with_qty in test_cases:
    results, report = detect_vegetables(
        text=text,
        vegetable_aliases=catalog.vegetable_aliases,
        vegetable_tamil_map=catalog.vegetable_tamil_map,
        noise_line_patterns=catalog.noise_line_patterns,
        return_details=True,
        confidence_threshold=75,
        client_name=client_name
    )
    
    extracted_count = len(results)
    with_qty_count = sum(1 for item in results if item['Quantity'])
    
    passed = extracted_count == expected_items and with_qty_count == expected_with_qty
    status = "✅ PASS" if passed else "❌ FAIL"
    
    print(f"\n{status} {format_name}")
    print(f"     Parser: {report.get('parser_strategy', 'N/A')}")
    print(f"     Expected: {expected_items} items, {expected_with_qty} with qty")
    print(f"     Got:      {extracted_count} items, {with_qty_count} with qty")
    
    if not passed:
        all_passed = False
        print("     Items:")
        for item in results:
            print(f"       - {item['Source Name']:20} | {item['Quantity']}")

print("\n" + "=" * 80)
if all_passed:
    print("🎉 ALL FORMATS VALIDATED: VIT, FVIT, Generic, and MRF extraction working!")
else:
    print("⚠️  Some formats failed validation")
print("=" * 80)
