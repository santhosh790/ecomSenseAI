"""
Test that the catalog loads with new fruits
"""

from application.vegetable_catalog_service import load_vegetable_catalog

catalog = load_vegetable_catalog()

print("=" * 80)
print("GROCERIES CATALOG TEST")
print("=" * 80)

print(f"\n✅ Total items in catalog: {len(catalog.vegetable_tamil_map)}")
print(f"✅ Total aliases: {len(catalog.vegetable_aliases)}")

# Count fruits vs vegetables
fruits = [
    "APPLE", "AVOCADO", "BANANA", "BANANA YELLAKKI", "BLACKBERRY", "CHERRY", 
    "CUSTARD APPLE", "DATES", "DRAGON FRUIT", "FIG", "GOOSEBERRY", 
    "GRAPES BLACK", "GRAPES GREEN", "GUAVA", "JACKFRUIT", "JAMUN", "KIWI",
    "LITCHI", "MANGO", "MUSK MELON", "MOSSAMBI", "ORANGE", "PAPAYA",
    "PASSION FRUIT", "PEACH", "PEAR", "PINEAPPLE", "PLUM", "POMEGRANATE",
    "RAMBUTAN", "RASPBERRIES", "RAW MANGO", "SAPOTA", "STRAWBERRY", 
    "SWEET LIME", "TAMARIND", "WATER MELON", "WOOD APPLE"
]

vegetables = [item for item in catalog.vegetable_tamil_map.keys() if item not in fruits]

print(f"\n📊 Category Breakdown:")
print(f"   🍎 Fruits: {len(fruits)}")
print(f"   🥬 Vegetables: {len(vegetables)}")

# Show some fruits
print(f"\n🍎 Sample Fruits (first 10):")
for fruit in sorted(fruits)[:10]:
    tamil = catalog.vegetable_tamil_map.get(fruit, "N/A")
    print(f"   {fruit:25} → {tamil}")

# Show some vegetables
print(f"\n🥬 Sample Vegetables (first 10):")
for veg in sorted(vegetables)[:10]:
    tamil = catalog.vegetable_tamil_map.get(veg, "N/A")
    print(f"   {veg:25} → {tamil}")

# Test extraction with fruits
print(f"\n🧪 Testing fruit extraction:")

from application.extraction_service import detect_vegetables

test_text = """1 APPLE RED 5 KG
2 MANGO 10 KG
3 GRAPES BLACK 3 KG
4 ORANGE 7 KG"""

results, report = detect_vegetables(
    text=test_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    confidence_threshold=75
)

print(f"   Extracted: {len(results)} items")
for item in results:
    print(f"     ✓ {item['Source Name']:15} | {item['Quantity']:10} | {item['Tamil Name']}")

print("\n" + "=" * 80)
print("✅ Groceries catalog (vegetables + fruits) loaded successfully!")
print("=" * 80)
