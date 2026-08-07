"""Final validation - all extraction issues resolved"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

from application.extraction_service import extract_row_fields

print('=' * 80)
print('FINAL VALIDATION - ALL EXTRACTION ISSUES')
print('=' * 80)
print()

all_test_cases = [
    {
        'category': 'Original Issue 1: PDF Extraction',
        'input': '13 200.00 1100054 MUSHROOM FRESH 0.8 Kgs 250.00',
        'expected_material': 'MUSHROOM',
        'expected_qty': '0.8 KG'
    },
    {
        'category': 'Original Issue 2: Text prefix "to |"',
        'input': 'to | 206589 [GREEN CHILLY_UB_1X1KG KG 5.00| 08.08.2026',
        'expected_material': 'GREEN CHILLY',
        'expected_qty': '5 KG'
    },
    {
        'category': 'Original Issue 2: Text prefix "ai_|"',
        'input': 'ai_| 206392 [GARLIC DRY_UB_1xIKG KG 3.00| 08.08.2026',
        'expected_material': 'GARLIC',
        'expected_qty': '3 KG'
    },
    {
        'category': 'Original Issue 2: Text prefix "is_|"',
        'input': 'is_| 206580 [CUCUMBER HYBRID_UB_1X1KG KG 3.00] 08.08.2026',
        'expected_material': 'CUCUMBER',
        'expected_qty': '3 KG'
    },
    {
        'category': 'Original Issue 3: Truncated line',
        'input': '14 206889 [GREEN CHILLY_UB_1X1KG KG 5',
        'expected_material': 'GREEN CHILLY',
        'expected_qty': '5 KG'
    },
    {
        'category': 'New Issue: Text prefix "is _|" (with space)',
        'input': 'is _| 206580 [CUCUMBER HYBRID_UB_1X1KG KG 3.00] 08.08.2026',
        'expected_material': 'CUCUMBER',
        'expected_qty': '3 KG'
    },
    {
        'category': 'New Issue: Text prefix "io |"',
        'input': 'io | 206589 [GREEN CHILLY_UB_1X1KG KG 5.00| 08.08.2026',
        'expected_material': 'GREEN CHILLY',
        'expected_qty': '5 KG'
    },
    {
        'category': 'New Issue: Text prefix "ti_|"',
        'input': 'ti_| 206392 [GARLIC DRY_UB_1xIKG KG. 3.00| 08.08.2026',
        'expected_material': 'GARLIC',
        'expected_qty': '3 KG'
    },
]

passed = 0
failed = 0

for i, test in enumerate(all_test_cases, 1):
    print(f"Test {i}: {test['category']}")
    print(f"  Input: \"{test['input']}\"")
    
    material, quantity = extract_row_fields(test['input'])
    
    material_ok = test['expected_material'] in material.upper()
    qty_ok = quantity == test['expected_qty']
    
    if material_ok and qty_ok:
        print(f"  ✅ PASS")
        print(f"     Material: \"{material}\"")
        print(f"     Quantity: \"{quantity}\"")
        passed += 1
    else:
        print(f"  ❌ FAIL")
        if not material_ok:
            print(f"     Material: \"{material}\" (expected to contain \"{test['expected_material']}\")")
        if not qty_ok:
            print(f"     Quantity: \"{quantity}\" (expected \"{test['expected_qty']}\")")
        failed += 1
    print()

print('=' * 80)
print('FINAL SUMMARY')
print('=' * 80)
print(f'Total Tests: {len(all_test_cases)}')
print(f'Passed: {passed}')
print(f'Failed: {failed}')
print()

if failed == 0:
    print('🎉 ALL EXTRACTION ISSUES RESOLVED!')
    print()
    print('Key improvements:')
    print('1. Priority qty+unit extraction prevents picking prices (0.8 KG not 250 KG)')
    print('2. Text prefix handling for "to |", "ai_|", "is_|", "is _|", "io |", "ti_|"')
    print('3. Clean material extraction:')
    print('   - Removes leading brackets: [ ( {')
    print('   - Removes _UB_1X1KG and _UB_1xIKG patterns')
    print('   - Removes item codes (6-8 digits)')
    print('   - Removes prices (X.XX format)')
    print()
    print('Result: Clean vegetable names for accurate matching!')
else:
    print(f'⚠️  {failed} test(s) still failing')

print('=' * 80)
