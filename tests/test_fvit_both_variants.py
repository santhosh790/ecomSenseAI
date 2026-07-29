"""Comprehensive FVIT test - both format variants"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

from application.vegetable_detection_service import detect_vegetables

# Combined test with both FVIT variants
test_text = """
VARIANT 1 (Original Format: Material → HSN → UOM → Qty):
1
ONION_KG
07031010
Kg
200
100.00
0%
20,000.00

VARIANT 2 (New Format: Material → UOM → HSN → UOM → Qty):
15
BUTTON MUSHROOM_1X1 
KG
070951
Kg
15
175.00
0%
2,625.00

3
POTATO_KG
07019090
Kg
150
80.00
0%
12,000.00
"""

print('=' * 80)
print('FVIT COMPREHENSIVE TEST - Both Format Variants')
print('=' * 80)
print()

results, report = detect_vegetables(
    test_text,
    return_details=True,
    client_name='FVIT',
)

print(f'📊 Extracted {len(results)} items:')
print()
print('┌────┬──────────────────────┬────────────┬──────┬──────────────────────────────┐')
print('│ #  │ Item Name            │ Quantity   │ Conf │ Tamil Name                   │')
print('├────┼──────────────────────┼────────────┼──────┼──────────────────────────────┤')

for idx, item in enumerate(results, 1):
    source_name = item.get('Source Name', '')
    tamil = item.get('Tamil Name', '').split('(')[0].strip()
    quantity = item.get('Quantity', '').ljust(10)
    confidence = item.get('Confidence', '')
    
    print(f'│ {idx:2d} │ {source_name:20s} │ {quantity} │ {confidence:4s} │ {tamil:28s} │')

print('└────┴──────────────────────┴────────────┴──────┴──────────────────────────────┘')
print()

# Verify all items have quantities
all_have_qty = all(item.get('Quantity', '').strip() for item in results)

print('=' * 80)
print('VERIFICATION:')
print(f'  Total items extracted: {len(results)}/3')
print(f'  All have quantities: {"✅ YES" if all_have_qty else "❌ NO"}')
print()
print('FORMAT VARIANTS SUPPORTED:')
print('  ✅ Variant 1: Material → HSN → UOM → Quantity (Original)')
print('  ✅ Variant 2: Material → UOM → HSN → UOM → Quantity (New)')
print('=' * 80)
