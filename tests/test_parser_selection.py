"""
Test parser selection functionality
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

catalog = load_vegetable_catalog()

# Sample data for each parser
vit_sample = """1
1010010
ONION
07031020 KG 150.000
25.00"""

fvit_sample = """1
ONION_KG
070310
Kg
200
25.00"""

generic_sample = """4 |ONION BIG_UB_1X1KG KG 45 __| 25.07.2026"""

print("=" * 80)
print("PARSER SELECTION TEST")
print("=" * 80)

test_cases = [
    ("VIT Parser (client_name='VIT')", vit_sample, "VIT"),
    ("FVIT Parser (client_name='FVIT')", fvit_sample, "FVIT"),
    ("Generic Parser (client_name=None)", generic_sample, None),
]

for test_name, text, parser in test_cases:
    print(f"\n📋 {test_name}:")
    print("-" * 80)
    
    results, report = detect_vegetables(
        text=text,
        vegetable_aliases=catalog.vegetable_aliases,
        vegetable_tamil_map=catalog.vegetable_tamil_map,
        noise_line_patterns=catalog.noise_line_patterns,
        return_details=True,
        confidence_threshold=75,
        client_name=parser
    )
    
    parser_strategy = report.get('parser_strategy', 'N/A')
    extracted = len(results)
    with_qty = sum(1 for item in results if item['Quantity'])
    
    print(f"  Parser Strategy: {parser_strategy}")
    print(f"  Extracted: {extracted} items")
    print(f"  With Quantity: {with_qty} items")
    
    if results:
        for item in results:
            print(f"    ✓ {item['Source Name']:15} | {item['Quantity']}")
    
    status = "✅ PASS" if extracted > 0 and with_qty > 0 else "❌ FAIL"
    print(f"  {status}")

print("\n" + "=" * 80)
print("✅ Parser selection test complete!")
print("=" * 80)
