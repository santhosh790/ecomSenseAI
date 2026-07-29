"""Test FVIT BUTTON MUSHROOM extraction issue"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

from application.vegetable_detection_service import detect_vegetables

# User's data showing BUTTON MUSHROOM not being extracted
test_text = """
15
BUTTON MUSHROOM_1X1 
KG
070951
Kg
15
175.00
0%
2,625.00
"""

print('=' * 80)
print('FVIT BUTTON MUSHROOM Extraction Test')
print('=' * 80)
print()
print('Input format:')
print('  Line 1: 15 (Serial)')
print('  Line 2: BUTTON MUSHROOM_1X1 (Material)')
print('  Line 3: KG (UOM)')
print('  Line 4: 070951 (HSN - 6 digits)')
print('  Line 5: Kg (UOM again)')
print('  Line 6: 15 (Quantity)')
print('  Line 7: 175.00 (Rate)')
print('  Line 8: 0% (GST)')
print('  Line 9: 2,625.00 (Amount)')
print()

results, report = detect_vegetables(
    test_text,
    return_details=True,
    client_name='FVIT',
)

print('=' * 80)
print(f'Extraction Results: {len(results)} items found')
print('=' * 80)
print()

if results:
    for idx, item in enumerate(results, 1):
        print(f'{idx}. {item.get("Source Name", ""):<20s} | {item.get("Quantity", ""):<10s} | {item.get("Tamil Name", "")}')
    
    # Check if mushroom was found
    mushroom_found = any('MUSHROOM' in item.get('Source Name', '').upper() for item in results)
    print()
    if mushroom_found:
        print('✅ MUSHROOM EXTRACTED SUCCESSFULLY')
    else:
        print('❌ MUSHROOM NOT FOUND IN RESULTS')
else:
    print('❌ NO ITEMS EXTRACTED')
    print()
    print('ISSUE: The FVIT parser expects format:')
    print('  Material → HSN (6-8 digits) → UOM → Quantity')
    print()
    print('But this document has format:')
    print('  Material → UOM → HSN (6 digits) → UOM → Quantity')
    print()
    print('The HSN appears AFTER the first UOM, not before it.')
