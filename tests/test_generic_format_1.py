"""
Test generic format extraction
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

# Generic format from user
generic_text = """L&T CSTITRINING CENTRE

SLNO[Article Code| Article Description vom ary | _ DELIVERY
1_| 206627 [Tomato COUNTRY_UB_1XIKG KG 65.00] 08.08.2026
2_| 206578 [COCONUT FRESH_UB_1XINOS EA 100.00] 08.08.2026
3_|_ 206607 [onion 8ig_uB_1xiKe KG. 130.00] 08.08.2026
4 | 206610 [POTATO LARGE_UB_1X1KG KG 15.00] 08.08.2025
5_| 206573 [CARROT_UB_1x1KG KG 4,00 08.08.2026
6 | 206559 _|BEETROOT_UB_1xiKG KG 40.00 | 08.08.2026
7_|_206611_[RADISH WHITE_UB_DXIKG KG. 2.00[ 08.08.2026
8 | 206586 [GINGER FRESH_UB_1X1KG KG 3.00] 08.08.2026
9 | 206561 [BOTTLE GOURD_UB_1x1KG KG 3.00| 08.08.2026
io | 206589 [GREEN CHILLY_UB_1X1KG KG 5.00| 08.08.2026
ti_| 206392 [GARLIC DRY_UB_1xIKG KG. 3.00| 08.08.2026
12 | 206583 _ [CURRY LEAVES UB_1XIKG KG 0.50| 08.08.2026
13 | 206584 _[DRUMSTICK_UB_1XiKG KG 3.00| 08.08.2026
14 | 206579 [CORIANDER LEAVES_UB_1X1KG KG 1.00| 08.08.2026
15 | 206534 [BANANA YELLOW_UB_1XiNOS EA 70.00 08.08.2026
is | 206615 [RED PUMPKIN_UB_1X1KG KG 7.00| 08.08.2026
17_|_205605_[MINTLEAVES UB_1XIKG KG 1.00 | 08.08.2026
is _| 206580 [CUCUMBER HYBRID_UB_1X1KG KG 3.00] 08.08.2026
19 _| 206599 _[LEMON_UB_1x1KG KG. 0.50 | 08.08.2026
20 | 206541 _[POMOGRANATE_UB_1XIKG KG 0.50| 08.08.2026
2a | 206528 _|APPLE-IMPORTED_UB_1X1KG KG 0.50 | 08.08.2026
22 | 206581 [CUCUMBER MALABAR_UB_IXIKG | KG 4,00| 08.08.2026
23 | 209087 |BEANS FRESH RINGS UB 1XIKG KG. 1.00| 08.08.2026

"""


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
