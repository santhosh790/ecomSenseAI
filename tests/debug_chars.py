"""
Check character-by-character around KG
"""

import re

# Test rows that are failing
test_rows = [
    ("TOMATO", "3__ [TOMATO COUNTRY_UB_1X1KG KG 30__| 25.07.2026"),
    ("GINGER", "7_|GINGER FRESH_UB_1X1KG KG 3__| 25.07.2026"),
]

print("=" * 80)
print("CHARACTER-LEVEL DEBUG")
print("=" * 80)

for name, row in test_rows:
    compact = re.sub(r"\s+", " ", str(row)).strip()
    
    print(f"\n{name}:")
    print(f"  Compact: {compact}")
    
    # Find KG position
    kg_pos = compact.find(" KG ")
    if kg_pos != -1:
        # Show characters around KG
        start = max(0, kg_pos - 5)
        end = min(len(compact), kg_pos + 15)
        chunk = compact[start:end]
        
        print(f"  Around KG (pos {kg_pos}):")
        print(f"    Text: '{chunk}'")
        print(f"    Chars: {[f'{c}({ord(c)})' for c in chunk]}")
        
        # Check what comes after "KG "
        after_kg = compact[kg_pos+4:]
        print(f"  After 'KG ': '{after_kg}'")
        print(f"  First 10 chars: {[f'{c}({ord(c)})' for c in after_kg[:10]]}")
        
        # Try to match the quantity part
        qty_pattern = r"^\d+(?:\.\d+)?\b"
        qty_match = re.match(qty_pattern, after_kg)
        if qty_match:
            print(f"  ✓ Quantity pattern matches: '{qty_match.group(0)}'")
        else:
            print(f"  ✗ Quantity pattern doesn't match")
            
        # Try without word boundary
        qty_pattern_no_boundary = r"^\d+(?:\.\d+)?"
        qty_match_nb = re.match(qty_pattern_no_boundary, after_kg)
        if qty_match_nb:
            print(f"  ✓ Quantity (no \\b) matches: '{qty_match_nb.group(0)}'")
            print(f"    Next char after qty: '{after_kg[len(qty_match_nb.group(0))]}' (ord={ord(after_kg[len(qty_match_nb.group(0))])})")

print("\n" + "=" * 80)
