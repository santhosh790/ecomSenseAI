"""
Test MRF format extraction
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

# MRF format from user
mrf_text = """SITE [> MRF ARAKKONAM =| vom[>| 27-30
206564 |BRINJAL VARI_UB_1X1KG KG 50
206569 |[CABBAGE_UB_1X1KG Ko | 150
206573 |CARROT_UB_1X1KG KG 50
206578 [COCONUT FRESH_UB_1X1NOS|_EA 300
206579 [CORIANDER LEAVES_UB_1X1K|_KG 8
206583 [CURRY LEAVES_UB_1X1KG KG 8
206392 [GARLIC DRY_UB_1X1KG Broke|__KG 8
206586 |GINGER FRESH_UB_1X1KG KG 15
206589 [GREEN CHILLY_UB_1X1KG KG 2
206598 [LADIES FINGER_UB_1X1KG KG 65
206607 |ONION BIG_UB_1X1KG Ke | 250
206610 | POTATO LARGE_UB_1X1KG Ke | 250
206611 [RADISH WHITE_UB_1X1KG KG 50
206627 |TOMATO COUNTRY_UB_1X1Kq KG | 250"""

catalog = load_vegetable_catalog()

print("=" * 80)
print("MRF FORMAT TEST")
print("=" * 80)

# Test without client name (generic parser)
results, report = detect_vegetables(
    text=mrf_text,
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
    ("Brinjal", "50 KG"),
    ("Cabbage", "150 KG"),
    ("Carrot", "50 KG"),
    ("Coconut", "300 EA"),
    ("Coriander", "8 KG"),
    ("Curry Leaves", "8 KG"),
    ("Garlic", "8 KG"),
    ("Ginger", "15 KG"),
    ("Green Chilly", "2 KG"),
    ("Ladies Finger", "65 KG"),
    ("Onion", "250 KG"),
    ("Potato", "250 KG"),
    ("Radish", "50 KG"),
    ("Tomato", "250 KG"),
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
