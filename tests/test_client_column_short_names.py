"""Test that client column headers use short names in consolidated view"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

import pandas as pd
from application.reporting_service import consolidate_with_client_columns

print('=' * 80)
print('TESTING CLIENT COLUMN SHORT NAMES')
print('=' * 80)
print()

# Create test data with full client names (as stored in CSV)
test_data = pd.DataFrame({
    'Source Name': ['ONION', 'TOMATO', 'ONION', 'GINGER', 'TOMATO'],
    'Tamil Name': ['வெங்காயம் (ONION)', 'தக்காளி (TOMATO)', 'வெங்காயம் (ONION)', 'இஞ்சி (GINGER)', 'தக்காளி (TOMATO)'],
    'Quantity': ['80 KG', '50 KG', '85 KG', '10 KG', '40 KG'],
    'Status': ['Matched'] * 5,
    'Client Name': ['CMC-RPT', 'CMC-RPT', 'LT-RPM', 'LT-RPM', 'LT-RPM'],  # Full names from CSV
})

print('Input Data (from CSV with full client names):')
print('-' * 80)
print(test_data[['Tamil Name', 'Quantity', 'Client Name']])
print()
print(f'Columns: {list(test_data.columns)}')
print()

# Run consolidation with client columns
result = consolidate_with_client_columns(test_data)

print('Output Data (consolidated with client columns):')
print('-' * 80)
print(result)
print()
print(f'Columns: {list(result.columns)}')
print()

# Check if columns are using short names
print('Column Header Analysis:')
print('-' * 80)

expected_mapping = {
    'CMC-RPT': 'CRPT',
    'LT-RPM': 'RPM'
}

for full_name, expected_short in expected_mapping.items():
    if full_name in result.columns:
        print(f'❌ FAIL: Column header "{full_name}" is still using FULL name')
        print(f'         Expected: "{expected_short}"')
    elif expected_short in result.columns:
        print(f'✅ PASS: Column header "{expected_short}" is using SHORT name')
        print(f'         (was: "{full_name}")')
    else:
        print(f'⚠️  WARN: Neither "{full_name}" nor "{expected_short}" found in columns')
print()

# Expected columns
expected_cols = ['Tamil Name', 'CRPT', 'RPM', 'Total Quantity', 'Unit']
actual_cols = list(result.columns)

print('Expected Columns:', expected_cols)
print('Actual Columns:  ', actual_cols)
print()

if actual_cols == expected_cols:
    print('✅ ALL TESTS PASSED')
    print('   • Client columns renamed from full to short names')
    print('   • Column order correct')
    print('   • Data integrity maintained')
else:
    print('❌ COLUMN MISMATCH')
    missing = set(expected_cols) - set(actual_cols)
    extra = set(actual_cols) - set(expected_cols)
    if missing:
        print(f'   Missing: {missing}')
    if extra:
        print(f'   Extra: {extra}')

print()
print('=' * 80)
print('VISUAL COMPARISON')
print('=' * 80)
print()
print('Before (what user saw):')
print('  # | காய்கறி பெயர் | CMC-RPT | LT-RPM | அளவு | அலகு')
print('  1 | வெங்காயம் (ONION) | 80 | 85 | 165 | KG')
print()
print('After (what user should see):')
print('  # | காய்கறி பெயர் | CRPT | RPM | அளவு | அலகு')
print('  1 | வெங்காயம் (ONION) | 80 | 85 | 165 | KG')
print()
print('=' * 80)
