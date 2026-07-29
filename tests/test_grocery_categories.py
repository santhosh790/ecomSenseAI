"""Test extraction of new grocery items (dairy, eggs, meat, rice)"""

from application.vegetable_detection_service import detect_vegetables

# Test text with various grocery categories
test_text = """
1) 301234 |BUTTER AMUL_UB_1X1KG KG 5 | 29.07.2026
2) 302345 |PANEER FRESH_UB_1X1KG KG 2 | 29.07.2026
3) 303456 |MILK TONED_UB_1X1L L 10 | 29.07.2026
4) 304567 |CURD CUP_UB_1X1EA EA 20 | 29.07.2026
5) 305678 |CHEESE SLICE_UB_1X1PKT PKT 3 | 29.07.2026
6) 306789 |EGG BROWN_UB_1X1TRAY EA 30 | 29.07.2026
7) 307890 |CHICKEN BONELESS_UB_1X1KG KG 3 | 29.07.2026
8) 308901 |FISH FILLET_UB_1X1KG KG 2 | 29.07.2026
9) 309012 |MUTTON_UB_1X1KG KG 1.5 | 29.07.2026
10) 310123 |RICE BASMATI_UB_1X1KG KG 25 | 29.07.2026
11) 311234 |GHEE PURE_UB_1X1KG KG 1 | 29.07.2026
12) 312345 |YOGURT_UB_1X1KG KG 5 | 29.07.2026
"""

print("=" * 80)
print("Testing New Grocery Items Extraction")
print("=" * 80)

print("\n📄 Input Text:")
print(test_text)
print("-" * 80)

# Extract items
results, report = detect_vegetables(
    test_text,
    return_details=True,
    client_name=None  # Generic parser
)

print(f"\n📊 Extraction Results: {len(results)} items found\n")

# Categorize items
categories = {
    'Dairy': [],
    'Eggs': [],
    'Meat/Fish': [],
    'Grains': [],
    'Other': []
}

for item in results:
    name = item.get('Source Name', 'N/A')
    qty = item.get('Quantity', 'N/A')
    conf = item.get('Confidence', 'N/A')
    
    # Categorize
    if any(x in name.upper() for x in ['BUTTER', 'PANEER', 'MILK', 'CURD', 'CHEESE', 'GHEE', 'YOGURT']):
        categories['Dairy'].append((name, qty, conf))
    elif 'EGG' in name.upper():
        categories['Eggs'].append((name, qty, conf))
    elif any(x in name.upper() for x in ['CHICKEN', 'FISH', 'MUTTON']):
        categories['Meat/Fish'].append((name, qty, conf))
    elif 'RICE' in name.upper():
        categories['Grains'].append((name, qty, conf))
    else:
        categories['Other'].append((name, qty, conf))

# Display by category
for category, items in categories.items():
    if items:
        print(f"\n{category}:")
        print("-" * 40)
        for name, qty, conf in items:
            print(f"  ✓ {name}: {qty} (Confidence: {conf})")

# Summary
print("\n" + "=" * 80)
print("Summary:")
print("-" * 80)
total_detected = sum(len(items) for items in categories.values())
expected_count = len([line for line in test_text.strip().split('\n') if line.strip() and line[0].isdigit()])
print(f"Total items detected: {total_detected}/{expected_count}")

for category, items in categories.items():
    if items:
        print(f"  {category}: {len(items)} items")

# Verification
expected_items = {
    'BUTTER', 'PANEER', 'MILK TONED', 'CURD', 'CHEESE', 
    'EGG', 'CHICKEN', 'FISH', 'MUTTON', 'RICE', 'GHEE', 'YOGURT'
}

detected_items = {item.get('Source Name', '').upper().split()[0] for item in results if item.get('Source Name')}

print("\n" + "-" * 80)
if total_detected >= 10:
    print("✅ SUCCESS: New grocery categories working correctly!")
else:
    print(f"⚠️  Only {total_detected}/12 items detected")
    missing = expected_items - detected_items
    if missing:
        print(f"Missing: {missing}")

print("=" * 80)
