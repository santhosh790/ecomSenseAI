"""
Detailed debug of pattern matching
"""

import re

# Test specific rows
test_rows = [
    ("ONION", "4 |ONION BIG_UB_1X1KG KG 45 __| 25.07.2026"),
    ("POTATO", "2_|POTATO LARGE_UB_1X1KG KG 20 | 25.07.2026"),
    ("TOMATO", "3__ [TOMATO COUNTRY_UB_1X1KG KG 30__| 25.07.2026"),
    ("GINGER", "7_|GINGER FRESH_UB_1X1KG KG 3__| 25.07.2026"),
]

pattern = r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s*(.+?)\s+(KG|KGS|NOS|EA)\.?\s+(\d+(?:\.\d+)?)\b"

print("=" * 80)
print("PATTERN MATCHING DEBUG")
print("=" * 80)
print(f"\nPattern: {pattern}\n")

for name, row in test_rows:
    compact = re.sub(r"\s+", " ", str(row)).strip()
    match = re.search(pattern, compact, flags=re.IGNORECASE)
    
    print(f"\n{name}:")
    print(f"  Row:     {row}")
    print(f"  Compact: {compact}")
    
    if match:
        print(f"  ✅ MATCH!")
        print(f"     Full match: '{match.group(0)}'")
        print(f"     Material:   '{match.group(1)}'")
        print(f"     Unit:       '{match.group(2)}'")
        print(f"     Quantity:   '{match.group(3)}'")
    else:
        print(f"  ❌ NO MATCH")
        
        # Try to see where it fails
        partial_patterns = [
            (r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}", "Serial number"),
            (r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*", "Serial + decorations"),
            (r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s*", "Serial + decorations + space"),
            (r"^\s*[\[\(\{\|_\-]*\s*\d{1,4}[\.)\]|_:\-]*\s*(.+?)\s+(?:KG|KGS|NOS|EA)", "Up to UOM"),
        ]
        
        for partial_pattern, description in partial_patterns:
            partial_match = re.search(partial_pattern, compact, flags=re.IGNORECASE)
            if partial_match:
                print(f"     ✓ {description}: '{partial_match.group(0)}'")
            else:
                print(f"     ✗ {description}: FAILED")
                break

print("\n" + "=" * 80)
