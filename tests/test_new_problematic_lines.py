"""Test the new problematic lines"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

from application.extraction_service import extract_row_fields

print('=' * 80)
print('TESTING NEW PROBLEMATIC LINES')
print('=' * 80)
print()

test_lines = [
    "is _| 206580 [CUCUMBER HYBRID_UB_1X1KG KG 3.00] 08.08.2026",
    "io | 206589 [GREEN CHILLY_UB_1X1KG KG 5.00| 08.08.2026",
    "ti_| 206392 [GARLIC DRY_UB_1xIKG KG. 3.00| 08.08.2026",
]

for i, line in enumerate(test_lines, 1):
    print(f'Test {i}:')
    print(f'Input: "{line}"')
    
    material, quantity = extract_row_fields(line)
    
    print(f'Output:')
    print(f'  Material: "{material}"')
    print(f'  Quantity: "{quantity}"')
    
    if material and quantity:
        print(f'  ✅ Extracted successfully')
    else:
        print(f'  ❌ Failed to extract')
    print()

# Debug: Check what happens after packaging removal
print('=' * 80)
print('DEBUG: After packaging removal')
print('=' * 80)
print()

import re

for line in test_lines:
    print(f'Original: "{line}"')
    compact = re.sub(r"\s+", " ", str(line)).strip()
    print(f'After whitespace: "{compact}"')
    compact = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", compact, flags=re.IGNORECASE)
    compact = re.sub(r"\s+", " ", compact).strip()
    print(f'After packaging removal: "{compact}"')
    print()

print('=' * 80)
