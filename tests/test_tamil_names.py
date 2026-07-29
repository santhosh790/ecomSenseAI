"""Test extraction of common grocery items to verify Tamil names appear"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

from application.vegetable_detection_service import detect_vegetables

test_text = """
1) TOMATO KG 30
2) CORIANDER KG 2
3) GINGER KG 5
4) GREEN CHILLY KG 1
5) MINT KG 0.5
6) SAMBAR ONION KG 10
7) BEANS FRENCH KG 8
8) CABBAGE KG 15
9) BANANA EA 50
10) LADY FINGER KG 6
11) RADISH KG 4
"""

print('=' * 80)
print('Testing Common Item Names with Tamil Translation')
print('=' * 80)
print()

results, report = detect_vegetables(test_text, return_details=True, client_name=None)

print(f'📊 Found {len(results)} items:')
print()

all_have_tamil = True
for idx, item in enumerate(results, 1):
    source_name = item.get('Source Name', '')
    tamil_name = item.get('Tamil Name', '')
    quantity = item.get('Quantity', '')
    confidence = item.get('Confidence', '')
    
    has_tamil = bool(tamil_name and tamil_name.strip())
    status_icon = '✅' if has_tamil else '❌'
    
    print(f'{idx}. {status_icon} {source_name:20s} | {quantity:10s} | {confidence:4s} | {tamil_name}')
    
    if not has_tamil:
        all_have_tamil = False

print()
print('=' * 80)
if all_have_tamil:
    print('✅ SUCCESS: All items have Tamil translations!')
else:
    print('❌ FAILURE: Some items missing Tamil translations')
print('=' * 80)
