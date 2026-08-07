"""Test extraction issues reported by user"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

from application.extraction_service import extract_row_fields, build_row_candidates, extract_row_quantity

print('=' * 80)
print('TESTING EXTRACTION ISSUES')
print('=' * 80)
print()

# Issue 1: PDF Extraction - Mushroom
print('Issue 1: PDF Extraction - Mushroom')
print('-' * 80)
test_line_1 = "13 200.00 1100054 MUSHROOM FRESH 0.8 Kgs 250.00"
print(f'Input: "{test_line_1}"')
material, quantity = extract_row_fields(test_line_1)
print(f'Output: material="{material}", quantity="{quantity}"')
print(f'Expected: quantity="0.8 KG"')
if quantity == "0.8 KG":
    print('✅ PASS')
else:
    print(f'❌ FAIL: Got "{quantity}" instead of "0.8 KG"')
print()

# Issue 2: Image extraction - Lines with prefix
print('Issue 2: Image extraction - Lines starting with text')
print('-' * 80)
test_lines_2 = [
    "to | 206589 [GREEN CHILLY_UB_1X1KG KG 5.00| 08.08.2026",
    "ai_| 206392 [GARLIC DRY_UB_1xIKG KG 3.00| 08.08.2026",
    "is_| 206580 [CUCUMBER HYBRID_UB_1X1KG KG 3.00] 08.08.2026"
]

noise_patterns = [
    r"^date",
    r"^total",
    r"^page",
    r"^invoice",
    r"^bill"
]

for test_line in test_lines_2:
    print(f'Input: "{test_line}"')
    
    # Try to extract directly
    material, quantity = extract_row_fields(test_line)
    print(f'  Direct extract: material="{material}", quantity="{quantity}"')
    
    # Try as candidate
    candidates = build_row_candidates([test_line], noise_patterns)
    print(f'  Candidates: {candidates}')
    
    if candidates:
        for cand in candidates:
            mat, qty = extract_row_fields(cand)
            print(f'    Candidate extract: material="{mat}", quantity="{qty}"')
    
    # What should work: extract green chilly/garlic/cucumber with proper quantity
    expected_veggie = "GREEN CHILLY" if "GREEN CHILLY" in test_line else ("GARLIC" if "GARLIC" in test_line else "CUCUMBER")
    if material and expected_veggie.split()[0] in material.upper():
        print(f'  ✅ PASS: Found {expected_veggie}')
    else:
        print(f'  ❌ FAIL: Did not extract {expected_veggie}')
    print()

# Issue 3: Image extraction - Truncated line
print('Issue 3: Image extraction - Truncated line')
print('-' * 80)
test_line_3 = "14 206889 [GREEN CHILLY_UB_1X1KG KG 5"
print(f'Input: "{test_line_3}"')
material, quantity = extract_row_fields(test_line_3)
print(f'Output: material="{material}", quantity="{quantity}"')
if "GREEN CHILLY" in material.upper() or "CHILLY" in material.upper():
    print('✅ PASS: Found GREEN CHILLY')
else:
    print('❌ FAIL: Did not extract GREEN CHILLY')
print()

# Additional diagnostics
print('=' * 80)
print('DIAGNOSTICS')
print('=' * 80)
print()

# Test the serial row pattern
import re
serial_row_pattern = r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s*"

print('Testing serial_row_pattern:')
print(f'Pattern: {serial_row_pattern}')
print()

test_patterns = [
    "14 206889 [GREEN CHILLY_UB_1X1KG KG 5",
    "to | 206589 [GREEN CHILLY_UB_1X1KG KG 5.00| 08.08.2026",
    "ai_| 206392 [GARLIC DRY_UB_1xIKG KG 3.00| 08.08.2026",
]

for line in test_patterns:
    match = re.match(serial_row_pattern, line)
    if match:
        print(f'✓ Matches: "{line}"')
        print(f'  Matched part: "{match.group()}"')
        print(f'  Remainder: "{line[match.end():]}"')
    else:
        print(f'✗ No match: "{line}"')
    print()

print('=' * 80)
