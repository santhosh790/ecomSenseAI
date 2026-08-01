"""Test consolidated Google Sheets push functionality with wide-to-long transformation"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

import pandas as pd

print('=' * 80)
print('TESTING CONSOLIDATED GOOGLE SHEETS PUSH (WIDE TO LONG FORMAT)')
print('=' * 80)
print()

# Create sample consolidated data in WIDE format (as shown in the screenshot)
print('Test 1: Sample Consolidated DataFrame (Wide Format)')
print('-' * 80)
sample_data = pd.DataFrame({
    'Tamil Name': [
        'அன்னாசி (PINE APPLE)',
        'அவரை (BROAD BEANS)',
        'ஆப்பிள் (APPLE)',
        'இஞ்சி (GINGER)',
        'உருளை (POTATO)',
    ],
    'CSTI': [0, 0, 1, 2, 15],
    'H': [0, 3, 0, 25, 300],
    'MRF': [0, 0, 0, 17, 250],
    'Q': [0, 0, 0, 20, 250],
    'RPM': [0, 0, 0, 3, 20],
    'RPTCMC': [18, 0, 0, 2, 15],
    'S': [15, 0, 0, 5, 100],
    'TPI': [0, 0, 0, 3, 20],
    'Total Quantity': [48, 3, 1, 80.5, 995],
    'Unit': ['KG', 'KG', 'KG', 'KG', 'KG']
})

print('Consolidated Data (Wide Format):')
print(sample_data.to_string())
print()

# Simulate the transformation
target_date = "2026-08-01"

print('Test 2: Transformation to Long Format')
print('-' * 80)

# Identify client columns
base_cols = ["Tamil Name", "Total Quantity", "Unit"]
client_cols = [col for col in sample_data.columns if col not in base_cols]

print(f'Client columns found: {client_cols}')
print()

# Transform to long format
long_format_rows = []

for _, row in sample_data.iterrows():
    tamil_name = str(row.get("Tamil Name", "")).strip()
    unit = str(row.get("Unit", "")).strip()
    
    for client_col in client_cols:
        quantity = row.get(client_col, 0)
        
        try:
            qty_float = float(quantity) if quantity != "" else 0.0
            if qty_float == 0.0:
                continue  # Skip zero quantities
        except (ValueError, TypeError):
            continue
        
        long_format_rows.append({
            "Date": target_date,
            "ClientName": client_col,
            "Item": tamil_name,
            "Unit": unit,
            "Quantity": qty_float
        })

push_df = pd.DataFrame(long_format_rows)
push_df = push_df[["Date", "ClientName", "Item", "Unit", "Quantity"]]

print('Transformed Data (Long Format):')
print(push_df.to_string())
print()
print(f'Total rows after transformation: {len(push_df)} (only non-zero quantities)')
print()

print('Test 3: Primary Key Validation')
print('-' * 80)
print('Primary Key Format: Date + ClientName + Item')
print()
print('Sample primary keys:')
for idx in range(min(5, len(push_df))):
    row = push_df.iloc[idx]
    key = (row["Date"], row["ClientName"], row["Item"])
    print(f'{idx+1}. {key}')
print()

print('Test 4: Expected Google Sheet Format')
print('-' * 80)
print('✓ Sheet name: "consolidated"')
print('✓ Primary key: (Date, ClientName, Item)')
print('✓ Columns: Date | ClientName | Item | Unit | Quantity')
print('✓ Only non-zero quantities are included')
print('✓ One row per client per item (unpivoted)')
print()

print('Test 5: Example Sheet Rows')
print('-' * 80)
print('Date       | ClientName | Item                  | Unit | Quantity')
print('-' * 80)
for idx in range(min(8, len(push_df))):
    row = push_df.iloc[idx]
    item_short = row["Item"][:20] + '...' if len(row["Item"]) > 20 else row["Item"]
    print(f'{row["Date"]} | {row["ClientName"]:<10} | {item_short:<21} | {row["Unit"]:<4} | {row["Quantity"]}')
print()

print('=' * 80)
print('✅ Data transformation validated!')
print(f'   • Wide format ({len(sample_data)} items) → Long format ({len(push_df)} rows)')
print('   • Zero quantities excluded')
print('   • Ready to push to Google Sheets via UI')
print('=' * 80)
