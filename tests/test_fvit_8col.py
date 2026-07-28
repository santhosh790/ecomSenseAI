"""
Test FVIT extraction with real 8-column format.
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

# FVIT format: 8 columns (Serial | Material | HSN | UOM | Qty | Rate | GST% | Amount)
fvit_8col_text = """1
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
3,000.00
3
TOMATO_KG
070210
Kg
100
30.00
0%
3,000.00"""

catalog = load_vegetable_catalog()

print("=" * 80)
print("FVIT 8-Column Format Test")
print("=" * 80)

results, report = detect_vegetables(
    text=fvit_8col_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    confidence_threshold=75,
    client_name="FVIT"
)

print(f"\n📊 Extraction Report:")
print(f"  Client Name: FVIT")
print(f"  Parser Strategy: {report.get('parser_strategy', 'N/A')}")
print(f"  Mode Activated: {report.get('vit_mode_activated', False)}")
print(f"  Activation Reason: {report.get('vit_activation_reason', 'N/A')}")
print(f"  Candidates Found: {report.get('candidate_lines', 0)}")
print(f"  Extracted Rows: {report.get('extracted_rows', 0)}")
print(f"  With Quantity: {report.get('with_quantity', 0)}")

print(f"\n✅ Extracted Items ({len(results)}):")
print("-" * 80)
for item in results:
    print(f"  {item['Source Name']:25} | {item['Quantity']:15} | {item['Confidence']:3}% | {item['Status']}")

if len(results) == 3 and all(item['Quantity'] for item in results):
    print("\n🎉 FVIT 8-column format extraction working!")
    expected_qtys = ["200 KG", "150 KG", "100 KG"]
    actual_qtys = [item['Quantity'] for item in results]
    if all(expected in actual_qtys for expected in expected_qtys):
        print("   ✅ All quantities extracted correctly!")
    else:
        print(f"   ⚠️  Quantity mismatch: Expected {expected_qtys}, Got {actual_qtys}")
else:
    print(f"\n⚠️  Expected 3 items with quantities, got {len(results)}")

print("\n" + "=" * 80)
