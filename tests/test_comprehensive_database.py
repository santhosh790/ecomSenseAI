"""Test comprehensive grocery database loading and categorization"""

from infrastructure.vegetable_catalog_repository import load_vegetable_catalog

# Load the catalog
catalog = load_vegetable_catalog()
items = catalog.vegetable_tamil_map
aliases = catalog.vegetable_aliases

print("=" * 80)
print("COMPREHENSIVE GROCERY DATABASE - STATISTICS")
print("=" * 80)

# Count items by category
categories = {
    'Fruits': [],
    'Vegetables': [],
    'Greens/Herbs': [],
    'Dairy/Eggs/Meat': [],
    'Grains/Legumes': [],
    'Spices/Seasonings': [],
    'Non-Food Items': [],
    'Other': []
}

for item in items.keys():
    item_upper = item.upper()
    
    # Categorize
    if any(x in item_upper for x in ['APPLE', 'MANGO', 'BANANA', 'GRAPE', 'ORANGE', 'BERRY', 'LYCHEE', 'GUAVA', 'PAPAYA', 'KIWI', 'MELON', 'POMEGRANATE', 'FIG', 'DATES', 'JACK FRUIT', 'PINEAPPLE', 'DRAGON', 'CUSTARD', 'RAMBUTAN', 'PLUM', 'PEAR']):
        categories['Fruits'].append(item)
    elif any(x in item_upper for x in ['GREENS', 'BASIL', 'CORIANDER', 'MINT', 'CURRY LEAVES', 'FENUGREEK', 'PARSLEY', 'THYME', 'ROSE MARY', 'DIL', 'METHI']):
        categories['Greens/Herbs'].append(item)
    elif any(x in item_upper for x in ['MILK', 'CURD', 'PANEER', 'EGG', 'CHICKEN', 'FISH', 'MUTTON', 'BUTTER', 'CHEESE', 'GHEE', 'YOGURT', 'DAHI']):
        categories['Dairy/Eggs/Meat'].append(item)
    elif any(x in item_upper for x in ['RICE', 'BEANS', 'PEAS', 'GROUNDNUT', 'PIGEON']):
        categories['Grains/Legumes'].append(item)
    elif any(x in item_upper for x in ['GARLIC', 'GINGER', 'CHILLI', 'CUMIN', 'TAMARIND', 'SALT', 'SUGAR', 'SODA']):
        categories['Spices/Seasonings'].append(item)
    elif any(x in item_upper for x in ['BAG', 'BASKET', 'CRATE', 'PAPER', 'TIN', 'TOWEL', 'GRINDER', 'TRANSPORT', 'WAGE', 'POOJA', 'CHOCOLATE', 'FLOWER']):
        categories['Non-Food Items'].append(item)
    else:
        categories['Vegetables'].append(item)

# Print summary
print(f"\n📊 DATABASE SUMMARY:")
print("-" * 80)
print(f"Total Items: {len(items)}")
print(f"Total Aliases: {len(aliases)}")
print()

# Print by category
for category, items_list in sorted(categories.items()):
    if items_list:
        print(f"\n{category}: {len(items_list)} items")
        print("-" * 40)
        # Show first 10 items in each category as examples
        for item in sorted(items_list)[:10]:
            tamil = items.get(item, "")
            print(f"  • {item}")
        if len(items_list) > 10:
            print(f"  ... and {len(items_list) - 10} more")

# Test a few specific items
print("\n" + "=" * 80)
print("SAMPLE ITEM LOOKUPS:")
print("-" * 80)

test_items = [
    'BANANA LEAF',
    'ONION SMALL',
    'TOMATO CHERRY',
    'GRAPES SEEDLESS BLACK',
    'CAULIFLOWER WITHOUT LEAF',
    'MANGO RAW BANGALORE',
    'GREENS AMARANTH'
]

for test_item in test_items:
    if test_item in items:
        print(f"✓ {test_item}: {items[test_item]}")
    else:
        print(f"✗ {test_item}: NOT FOUND")

print("\n" + "=" * 80)
print("✅ DATABASE LOADED SUCCESSFULLY!")
print("=" * 80)
