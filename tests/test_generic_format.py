"""
Test generic format extraction
"""

from application.extraction_service import detect_vegetables
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

print("=" * 80)
print("GENERIC FORMAT TEST")
print("=" * 80)

# Test without client name (generic parser)
results, report = detect_vegetables(
    text=generic_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    confidence_threshold=75,
    client_name=None
)

print(f"\n📊 Extraction Report:")
print(f"  Parser Strategy: {report.get('parser_strategy', 'N/A')}")
print(f"  Candidates Found: {report.get('candidate_lines', 0)}")
print(f"  Extracted Rows: {report.get('extracted_rows', 0)}")
print(f"  With Quantity: {report.get('with_quantity', 0)}")

print(f"\n✅ Extracted Items ({len(results)}):")
print("-" * 80)
if results:
    for item in results:
        print(f"  {item['Source Name']:25} | {item['Quantity']:15} | {item['Confidence']:3}% | {item['Status']}")
else:
    print("  No items extracted!")

# Expected items
expected_items = [
    ("Onion", "45 KG"),
    ("Potato", "20 KG"),
    ("Tomato", "30 KG"),
    ("Cabbage", "6 KG"),
    ("Ladies Finger", "5 KG"),
    ("Garlic", "4 KG"),
    ("Ginger", "3 KG"),
    ("Green Chilly", "2 KG"),
    ("Beetroot", "65 KG"),
    ("Coriander", "1 KG"),
    ("Brinjal", "6 KG"),
    ("Raw Mango", "10 KG"),
    ("Chow Chow", "35 KG"),
    ("Radish", "20 KG"),
    ("Curry Leaves", "1.5 KG"),
    ("Coconut", "80 EA"),
    ("Beans", "12 KG"),
]

print(f"\n📋 Expected: {len(expected_items)} items")
print(f"   Extracted: {len(results)} items")

missing = []
for name, qty in expected_items:
    found = any(name.lower() in item['Source Name'].lower() for item in results)
    if not found:
        missing.append(f"{name} ({qty})")

if missing:
    print(f"\n❌ Missing items ({len(missing)}):")
    for item in missing:
        print(f"   - {item}")
else:
    print(f"\n✅ All items found!")

# Check quantities
items_without_qty = [item['Source Name'] for item in results if not item['Quantity']]
if items_without_qty:
    print(f"\n⚠️  Items without quantity ({len(items_without_qty)}):")
    for item in items_without_qty:
        print(f"   - {item}")

print("\n" + "=" * 80)
