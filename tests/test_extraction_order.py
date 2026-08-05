"""Test that consolidation preserves original extraction order"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

import pandas as pd
from application.reporting_service import consolidate, consolidate_with_client_columns

print('=' * 80)
print('TESTING ORIGINAL EXTRACTION ORDER PRESERVATION')
print('=' * 80)
print()

# Create sample data in specific extraction order (NOT alphabetical)
print('Test 1: Original Extraction Order')
print('-' * 80)
sample_data = pd.DataFrame({
    'Tamil Name': [
        'வெங்காயம் (ONION)',       # 1. ONION
        'தக்காளி (TOMATO)',         # 2. TOMATO
        'வெங்காயம் (ONION)',       # 1. ONION (duplicate)
        'இஞ்சி (GINGER)',           # 3. GINGER
        'கேரட் (CARROT)',           # 4. CARROT
        'தக்காளி (TOMATO)',         # 2. TOMATO (duplicate)
        'இஞ்சி (GINGER)',           # 3. GINGER (duplicate)
        'ஆப்பிள் (APPLE)',          # 5. APPLE (fruit)
    ],
    'Quantity': [10, 15, 5, 20, 8, 10, 5, 12],
    'Unit': ['KG'] * 8,
    'Client Name': ['A', 'A', 'B', 'A', 'A', 'B', 'B', 'A']
})

print('Original data (extraction order):')
print(sample_data[['Tamil Name', 'Quantity', 'Client Name']])
print()
print('Expected order after consolidation:')
print('  1. வெங்காயம் (ONION) - appeared first')
print('  2. தக்காளி (TOMATO) - appeared second')
print('  3. இஞ்சி (GINGER) - appeared third')
print('  4. கேரட் (CARROT) - appeared fourth')
print('  5. ஆப்பிள் (APPLE) - appeared fifth')
print()

# Test basic consolidation
print('Test 2: Consolidate (without client columns)')
print('-' * 80)
consolidated = consolidate(sample_data)
print('Consolidated result:')
print(consolidated)
print()

# Verify order
expected_order = [
    'வெங்காயம் (ONION)',
    'தக்காளி (TOMATO)',
    'இஞ்சி (GINGER)',
    'கேரட் (CARROT)',
    'ஆப்பிள் (APPLE)',
]

actual_order = consolidated['Tamil Name'].tolist()
print('Order verification:')
print(f'  Expected: {expected_order}')
print(f'  Actual:   {actual_order}')
print(f'  Match: {actual_order == expected_order}')
print()

# Test consolidation with client columns
print('Test 3: Consolidate with client columns')
print('-' * 80)
consolidated_clients = consolidate_with_client_columns(sample_data)
print('Consolidated result with clients:')
print(consolidated_clients)
print()

# Verify order in client consolidation
actual_order_clients = consolidated_clients['Tamil Name'].tolist()
print('Order verification:')
print(f'  Expected: {expected_order}')
print(f'  Actual:   {actual_order_clients}')
print(f'  Match: {actual_order_clients == expected_order}')
print()

# Test with mixed order (fruits and vegetables)
print('Test 4: Mixed Order (Fruit → Vegetable → Fruit → Vegetable)')
print('-' * 80)
mixed_data = pd.DataFrame({
    'Tamil Name': [
        'ஆப்பிள் (APPLE)',          # 1. APPLE (fruit first!)
        'கேரட் (CARROT)',           # 2. CARROT (vegetable)
        'வாழைப்பழம் (BANANA)',      # 3. BANANA (fruit)
        'வெங்காயம் (ONION)',       # 4. ONION (vegetable)
    ],
    'Quantity': [10, 15, 20, 25],
    'Unit': ['KG'] * 4
})

print('Original mixed order:')
print(mixed_data[['Tamil Name', 'Quantity']])
print()

consolidated_mixed = consolidate(mixed_data)
print('Consolidated result (should preserve mixed order):')
print(consolidated_mixed)
print()

expected_mixed_order = [
    'ஆப்பிள் (APPLE)',
    'கேரட் (CARROT)',
    'வாழைப்பழம் (BANANA)',
    'வெங்காயம் (ONION)',
]
actual_mixed_order = consolidated_mixed['Tamil Name'].tolist()
print('Order verification:')
print(f'  Expected: {expected_mixed_order}')
print(f'  Actual:   {actual_mixed_order}')
print(f'  Match: {actual_mixed_order == expected_mixed_order}')
print()

print('=' * 80)
if actual_order == expected_order and actual_order_clients == expected_order and actual_mixed_order == expected_mixed_order:
    print('✅ SUCCESS! Original extraction order is preserved')
    print('   • Consolidation maintains first occurrence order')
    print('   • No alphabetical sorting applied')
    print('   • No category-based sorting (vegetables/fruits)')
    print('   • Mixed order (fruit→veg→fruit→veg) preserved')
else:
    print('❌ FAILED! Order not preserved correctly')
print('=' * 80)
