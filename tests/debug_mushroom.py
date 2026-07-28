"""
Debug mushroom extraction issue.
"""

mushroom_text = """190
206606
MUSHROOM
BUTTON
FRESH_UB_1X1
KG
07104000_
A
KG 20.000
200.00
"""

lines = [l.strip() for l in mushroom_text.splitlines() if l.strip()]

print("Mushroom lines:")
for i, line in enumerate(lines, 1):
    print(f"{i}. '{line}'")

# The issue: HSN is split across lines!
# Line 7: "07104000_"
# Line 8: "A" 
# Line 9: "KG 20.000"

# So the pattern "07104000_ A KG 20.000" needs to be matched, but they're on separate lines!
