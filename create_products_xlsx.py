"""Generate Excel file with products and aliases data"""
import json
import pandas as pd
from pathlib import Path

# Load JSON files
json_path = Path('data/products.json')
if not json_path.exists():
    json_path = Path('data/vegetables.json')

with open(json_path, 'r', encoding='utf-8') as f:
    products_data = json.load(f)

with open('data/aliases.json', 'r', encoding='utf-8') as f:
    aliases_data = json.load(f)

# Convert products data to DataFrame
products_list = []
mapping = products_data.get('product_tamil_map') or products_data.get('vegetable_tamil_map', {})
for item, tamil_name in mapping.items():
    # Extract Tamil name and English name from the format "தமிழ் (ENGLISH)"
    if '(' in tamil_name and ')' in tamil_name:
        tamil_only = tamil_name.split('(')[0].strip()
        english_from_tamil = tamil_name.split('(')[1].replace(')', '').strip()
    else:
        tamil_only = tamil_name
        english_from_tamil = item
    
    products_list.append({
        'Item Name': item,
        'Tamil Name': tamil_only,
        'Full Tamil Format': tamil_name
    })

products_df = pd.DataFrame(products_list)
products_df = products_df.sort_values('Item Name').reset_index(drop=True)
products_df.index = products_df.index + 1  # Start index from 1

# Convert aliases data to DataFrame
aliases_list = []
for alias, canonical in aliases_data.items():
    aliases_list.append({
        'Alias': alias,
        'Maps To': canonical
    })

aliases_df = pd.DataFrame(aliases_list)
aliases_df = aliases_df.sort_values(['Maps To', 'Alias']).reset_index(drop=True)
aliases_df.index = aliases_df.index + 1  # Start index from 1

# Create Excel file with multiple sheets
output_file = 'products_and_aliases.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Write products sheet
    products_df.to_excel(writer, sheet_name='Products', index=True, index_label='#')
    
    # Write aliases sheet
    aliases_df.to_excel(writer, sheet_name='Aliases', index=True, index_label='#')
    
    # Get workbook and worksheets for formatting
    workbook = writer.book
    products_sheet = writer.sheets['Products']
    aliases_sheet = writer.sheets['Aliases']
    
    # Auto-adjust column widths for products sheet
    for column in products_sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        products_sheet.column_dimensions[column_letter].width = adjusted_width
    
    # Auto-adjust column widths for aliases sheet
    for column in aliases_sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 40)
        aliases_sheet.column_dimensions[column_letter].width = adjusted_width

print('=' * 80)
print('EXCEL FILE GENERATION COMPLETE')
print('=' * 80)
print()
print(f'📄 Output File: {output_file}')
print()
print('📊 Summary:')
print(f'   Products Sheet: {len(products_df)} items')
print(f'   Aliases Sheet: {len(aliases_df)} mappings')
print()
print('📋 Sheets Created:')
print('   1. Vegetables - Contains all items with Tamil translations')
print('   2. Aliases - Contains all alias mappings to canonical names')
print()
print('✅ File ready for viewing/editing in Excel, Google Sheets, or LibreOffice')
print('=' * 80)
