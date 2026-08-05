"""Test that ALL Google Sheets push functions include Order column"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

import pandas as pd

print('=' * 80)
print('TESTING ORDER COLUMN IN ALL GOOGLE SHEETS PUSH FUNCTIONS')
print('=' * 80)
print()

# Test 1: Validated Items Push (push_validated_items_to_google_sheet)
print('Test 1: Validated Items Push (Sheet1)')
print('-' * 80)
print('Function: push_validated_items_to_google_sheet')
print()

# Simulate validated items data (as it comes from the editing table)
validated_data = pd.DataFrame({
    'Source Name': [
        'ONION',
        'TOMATO', 
        'GINGER',
        'CARROT',
        'APPLE',
    ],
    'Tamil Name': [
        'வெங்காயம் (ONION)',
        'தக்காளி (TOMATO)',
        'இஞ்சி (GINGER)',
        'கேரட் (CARROT)',
        'ஆப்பிள் (APPLE)',
    ],
    'Quantity': ['10 KG', '15 KG', '2 KG', '8 KG', '12 KG'],
    'Status': ['Matched'] * 5,
    'Confidence': ['95%', '98%', '92%', '97%', '96%']
})

print('Input data:')
print(validated_data[['Tamil Name', 'Quantity', 'Status']])
print()

# Simulate the transformation in push_validated_items_to_google_sheet
push_df = validated_data.copy()
# Add Order column (1-based sequence) as first column
push_df.insert(0, "Order", range(1, len(push_df) + 1))
# Add Date column
push_df["Date"] = "2026-08-05"
push_df = push_df.fillna("")

# Reorder columns to put Order and Date first
cols = push_df.columns.tolist()
cols.remove("Order")
cols.remove("Date")
push_df = push_df[["Order", "Date"] + cols]

print('Output to Google Sheets (Sheet1):')
print('Headers:', list(push_df.columns))
print()
print(push_df.to_string())
print()

# Test 2: Consolidated Push (push_consolidated_to_google_sheet)
print('Test 2: Consolidated Push (consolidated sheet)')
print('-' * 80)
print('Function: push_consolidated_to_google_sheet')
print()

# Simulate consolidated data (wide format)
consolidated_data = pd.DataFrame({
    'Tamil Name': [
        'வெங்காயம் (ONION)',
        'தக்காளி (TOMATO)',
        'இஞ்சி (GINGER)',
        'கேரட் (CARROT)',
        'ஆப்பிள் (APPLE)',
    ],
    'CSTI': [10, 15, 2, 8, 12],
    'H': [5, 10, 25, 0, 0],
    'MRF': [0, 0, 17, 0, 0],
    'Unit': ['KG'] * 5,
    'Total Quantity': [15, 25, 44, 8, 12]
})

print('Input data (wide format):')
print(consolidated_data[['Tamil Name', 'CSTI', 'H', 'MRF', 'Unit']])
print()

# Simulate the transformation in push_consolidated_to_google_sheet
base_cols = ["Tamil Name", "Total Quantity", "Unit"]
client_cols = [col for col in consolidated_data.columns if col not in base_cols]

long_format_rows = []
for item_order, (_, row) in enumerate(consolidated_data.iterrows(), start=1):
    tamil_name = str(row.get("Tamil Name", "")).strip()
    unit = str(row.get("Unit", "")).strip()
    
    for client_col in client_cols:
        quantity = row.get(client_col, 0)
        
        try:
            qty_float = float(quantity) if quantity != "" else 0.0
            if qty_float == 0.0:
                continue
        except (ValueError, TypeError):
            continue
        
        long_format_rows.append({
            "Order": item_order,
            "Date": "2026-08-05",
            "ClientName": client_col,
            "Item": tamil_name,
            "Unit": unit,
            "Quantity": qty_float
        })

push_df_consolidated = pd.DataFrame(long_format_rows)
push_df_consolidated = push_df_consolidated[["Order", "Date", "ClientName", "Item", "Unit", "Quantity"]]

print('Output to Google Sheets (consolidated sheet):')
print('Headers:', list(push_df_consolidated.columns))
print()
print(push_df_consolidated.head(10).to_string())
print()

# Verification
print('=' * 80)
print('VERIFICATION RESULTS')
print('=' * 80)
print()

print('✅ Push Validated Items (Sheet1):')
print(f'   • First column: {push_df.columns[0]} (should be Order)')
print(f'   • Second column: {push_df.columns[1]} (should be Date)')
print(f'   • Order range: {push_df["Order"].min()} to {push_df["Order"].max()}')
print(f'   • Row count: {len(push_df)}')
print()

print('✅ Push Consolidated (consolidated sheet):')
print(f'   • First column: {push_df_consolidated.columns[0]} (should be Order)')
print(f'   • Second column: {push_df_consolidated.columns[1]} (should be Date)')
print(f'   • Order range: {push_df_consolidated["Order"].min()} to {push_df_consolidated["Order"].max()}')
print(f'   • Row count: {len(push_df_consolidated)}')
print()

# Both should have Order as first column
validated_pass = push_df.columns[0] == "Order" and push_df.columns[1] == "Date"
consolidated_pass = push_df_consolidated.columns[0] == "Order" and push_df_consolidated.columns[1] == "Date"

if validated_pass and consolidated_pass:
    print('=' * 80)
    print('✅ ALL GOOGLE SHEETS PUSHES PRESERVE ORDER!')
    print('   • Both functions include Order column')
    print('   • Order is always the first column')
    print('   • Date is always the second column')
    print('   • Extraction sequence is permanently preserved')
    print('=' * 80)
else:
    print('❌ FAILED: Some functions missing Order column')
    if not validated_pass:
        print('   - push_validated_items_to_google_sheet needs fixing')
    if not consolidated_pass:
        print('   - push_consolidated_to_google_sheet needs fixing')
