"""Preview the generated Excel file"""
from pathlib import Path
import pandas as pd

# Read the Excel file
excel_file = 'products_and_aliases.xlsx'
if not Path(excel_file).exists():
    excel_file = 'vegetables_and_aliases.xlsx'

print('=' * 100)
print(f'EXCEL FILE PREVIEW: {excel_file}')
print('=' * 100)
print()

# Preview Products sheet
sheet_name = 'Products'
try:
    products_df = pd.read_excel(excel_file, sheet_name=sheet_name, index_col=0)
except Exception:
    sheet_name = 'Vegetables'
    products_df = pd.read_excel(excel_file, sheet_name=sheet_name, index_col=0)

print(f'📋 SHEET 1: {sheet_name} ({len(products_df)} items)')
print('─' * 100)
print()
print('First 10 items:')
print(products_df.head(10).to_string())
print()
print('...')
print()

# Preview Aliases sheet
print('=' * 100)
aliases_df = pd.read_excel(excel_file, sheet_name='Aliases', index_col=0)
print(f'📋 SHEET 2: Aliases ({len(aliases_df)} mappings)')
print('─' * 100)
print()
print('First 10 aliases:')
print(aliases_df.head(10).to_string())
print()
print('...')
print()

print('=' * 100)
print('✅ Excel file contains:')
print(f'   • {len(products_df)} items with Tamil translations')
print(f'   • {len(aliases_df)} alias mappings')
print()
print(f'📁 File: {excel_file}')
print('=' * 100)
