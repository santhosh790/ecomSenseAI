"""Test row-level deletion feature in validation"""
import pandas as pd

# Simulate the validation workflow
print("=" * 80)
print("ROW DELETION FEATURE TEST")
print("=" * 80)
print()

# Step 1: Create sample extracted data
initial_items = [
    {"Source Name": "Tomato", "Tamil Name": "தக்காளி (TOMATO)", "Quantity": "30 KG", "Status": "Auto Extracted", "Confidence": "99%"},
    {"Source Name": "Onion", "Tamil Name": "வெங்காயம் (ONION)", "Quantity": "50 KG", "Status": "Auto Extracted", "Confidence": "99%"},
    {"Source Name": "Potato", "Tamil Name": "உருளை (POTATO)", "Quantity": "25 KG", "Status": "Auto Extracted", "Confidence": "99%"},
    {"Source Name": "Carrot", "Tamil Name": "கேரட் (CARROT)", "Quantity": "10 KG", "Status": "Auto Extracted", "Confidence": "99%"},
    {"Source Name": "Cabbage", "Tamil Name": "முட்டைக்கோஸ் (CABBAGE)", "Quantity": "15 KG", "Status": "Auto Extracted", "Confidence": "99%"},
]

df = pd.DataFrame(initial_items)
print("Step 1: Initial Extraction")
print(f"  Total items extracted: {len(df)}")
print()

# Step 2: Add Delete column (as done in UI)
df.insert(0, "Delete", False)
print("Step 2: Add Delete Column")
print(f"  Columns: {list(df.columns)}")
print()

# Step 3: User marks some rows for deletion (simulating user action)
# Let's say user wants to delete Potato and Cabbage
df.loc[df["Source Name"] == "Potato", "Delete"] = True
df.loc[df["Source Name"] == "Cabbage", "Delete"] = True

print("Step 3: User Marks Rows for Deletion")
print("  User checked Delete for: Potato, Cabbage")
print()
print("  Current state:")
for idx, row in df.iterrows():
    delete_marker = "🗑️" if row["Delete"] else "  "
    print(f"    {delete_marker} {row['Source Name']:15s} | {row['Quantity']:10s} | Delete={row['Delete']}")
print()

# Step 4: Confirm button pressed - filter out deleted rows
rows_to_delete = df["Delete"].sum()
final_df = df[df["Delete"] == False].copy()
final_df = final_df.drop(columns=["Delete"])

print("Step 4: Confirmation (Filter Deleted Rows)")
print(f"  Rows marked for deletion: {rows_to_delete}")
print(f"  Final items to save: {len(final_df)}")
print()

# Step 5: Show final output (what goes to CSV)
print("Step 5: Final Output (Saved to CSV)")
print("-" * 80)
for idx, row in final_df.iterrows():
    print(f"  ✅ {row['Source Name']:15s} | {row['Quantity']:10s} | {row['Tamil Name']}")
print("-" * 80)
print()

# Verification
expected_items = ["Tomato", "Onion", "Carrot"]
actual_items = final_df["Source Name"].tolist()

print("=" * 80)
print("VERIFICATION:")
print(f"  Expected items: {expected_items}")
print(f"  Actual items:   {actual_items}")
print(f"  Match: {'✅ PASS' if actual_items == expected_items else '❌ FAIL'}")
print()

# Check that Delete column is removed
print(f"  'Delete' column removed: {'✅ PASS' if 'Delete' not in final_df.columns else '❌ FAIL'}")
print("=" * 80)
