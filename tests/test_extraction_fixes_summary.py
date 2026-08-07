"""Summary of extraction fixes"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

from application.extraction_service import extract_row_fields

print('=' * 80)
print('EXTRACTION FIXES SUMMARY')
print('=' * 80)
print()

test_cases = [
    {
        'name': 'Issue 1: PDF Extraction - Mushroom quantity',
        'input': '13 200.00 1100054 MUSHROOM FRESH 0.8 Kgs 250.00',
        'expected_qty': '0.8 KG',
        'expected_item': 'MUSHROOM'
    },
    {
        'name': 'Issue 2a: Text prefix - "to |"',
        'input': 'to | 206589 [GREEN CHILLY_UB_1X1KG KG 5.00| 08.08.2026',
        'expected_qty': '5 KG',
        'expected_item': 'GREEN CHILLY'
    },
    {
        'name': 'Issue 2b: Text prefix - "ai_|"',
        'input': 'ai_| 206392 [GARLIC DRY_UB_1xIKG KG 3.00| 08.08.2026',
        'expected_qty': '3 KG',
        'expected_item': 'GARLIC'
    },
    {
        'name': 'Issue 2c: Text prefix - "is_|"',
        'input': 'is_| 206580 [CUCUMBER HYBRID_UB_1X1KG KG 3.00] 08.08.2026',
        'expected_qty': '3 KG',
        'expected_item': 'CUCUMBER'
    },
    {
        'name': 'Issue 3: Truncated line',
        'input': '14 206889 [GREEN CHILLY_UB_1X1KG KG 5',
        'expected_qty': '5 KG',
        'expected_item': 'CHILLY'
    },
]

print('Test Results:')
print('-' * 80)
print()

passed = 0
failed = 0

for test in test_cases:
    print(f"Test: {test['name']}")
    print(f"Input: \"{test['input']}\"")
    
    material, quantity = extract_row_fields(test['input'])
    
    print(f"Output:")
    print(f"  Material: \"{material}\"")
    print(f"  Quantity: \"{quantity}\"")
    
    qty_ok = quantity == test['expected_qty']
    item_ok = test['expected_item'] in material.upper()
    
    if qty_ok and item_ok:
        print(f"✅ PASS")
        passed += 1
    else:
        print(f"❌ FAIL")
        if not qty_ok:
            print(f"  Quantity mismatch: expected \"{test['expected_qty']}\", got \"{quantity}\"")
        if not item_ok:
            print(f"  Item not found: expected \"{test['expected_item']}\" in \"{material}\"")
        failed += 1
    print()

print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'Passed: {passed}/{len(test_cases)}')
print(f'Failed: {failed}/{len(test_cases)}')
print()

if failed == 0:
    print('🎉 ALL TESTS PASSED!')
    print()
    print('Fixes implemented:')
    print('1. Priority fix: Extract quantity+unit pairs FIRST to avoid picking prices')
    print('   - Solves "13 200.00 1100054 MUSHROOM FRESH 0.8 Kgs 250.00" → 0.8 KG ✓')
    print()
    print('2. Text prefix handling: Added optional text prefix pattern to all regex')
    print('   - Pattern: ^(?:[A-Za-z_]+\\s*[\\|_\\-]+\\s*)?')
    print('   - Handles "to |", "ai_|", "is_|" prefixes before serial numbers ✓')
    print()
    print('3. Improved material extraction: Clean up item codes, prices, decorators')
    print('   - Removes serial numbers, item codes (6-8 digits), prices (X.XX)')
    print()
else:
    print('⚠️  Some tests failed. Review output above.')

print('=' * 80)
