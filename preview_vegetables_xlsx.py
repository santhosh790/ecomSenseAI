"""Preview the generated Excel file"""
import pandas as pd

# Read the Excel file
excel_file = 'vegetables_and_aliases.xlsx'

print('=' * 100)
print('EXCEL FILE PREVIEW: vegetables_and_aliases.xlsx')
print('=' * 100)
print()

# Preview Vegetables sheet
print('📋 SHEET 1: Vegetables (256 items)')
print('─' * 100)
vegetables_df = pd.read_excel(excel_file, sheet_name='Vegetables', index_col=0)
print()
print('First 10 items:')
print(vegetables_df.head(10).to_string())
print()
print('...')
print()
print('Sample Keerai items:')
keerai_df = vegetables_df[vegetables_df['Item Name'].str.contains('KEERAI', na=False)]
print(keerai_df.head(10).to_string())
print()

# Preview Aliases sheet
print('=' * 100)
print('📋 SHEET 2: Aliases (323 mappings)')
print('─' * 100)
aliases_df = pd.read_excel(excel_file, sheet_name='Aliases', index_col=0)
print()
print('First 10 aliases:')
print(aliases_df.head(10).to_string())
print()
print('...')
print()
print('Sample Keerai aliases:')
keerai_aliases = aliases_df[aliases_df['Alias'].str.contains('KEERAI', na=False)]
print(keerai_aliases.head(10).to_string())
print()

print('=' * 100)
print('✅ Excel file contains:')
print(f'   • {len(vegetables_df)} vegetables with Tamil translations')
print(f'   • {len(aliases_df)} alias mappings')
print(f'   • {len(keerai_df)} Keerai varieties')
print(f'   • {len(keerai_aliases)} Keerai aliases')
print()
print('📁 File: vegetables_and_aliases.xlsx (22 KB)')
print('=' * 100)
