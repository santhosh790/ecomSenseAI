"""Check which aliases are broken after database update"""
import json

# Load both files
with open('data/vegetables.json', 'r', encoding='utf-8') as f:
    db = json.load(f)
with open('data/aliases.json', 'r', encoding='utf-8') as f:
    aliases = json.load(f)

db_items = set(db['vegetable_tamil_map'].keys())

# Check critical aliases
critical_items = [
    'TOMATO', 'CORIANDER', 'GINGER', 'GREEN CHILLY', 'MINT', 
    'SAMBAR ONION', 'BEANS FRENCH', 'CABBAGE', 'BANANA', 
    'LADY FINGER', 'RADISH', 'GREEN CHILLI'
]

print('🔍 CRITICAL ALIAS ISSUES')
print('=' * 80)
broken = []
for item in critical_items:
    alias_target = aliases.get(item, 'NOT IN ALIASES')
    exists_in_db = alias_target in db_items if alias_target != 'NOT IN ALIASES' else False
    
    print(f'\n{item}:')
    print(f'  Alias points to: {alias_target}')
    print(f'  Exists in DB: {"✅" if exists_in_db else "❌"}')
    
    if not exists_in_db:
        broken.append((item, alias_target))
        # Find similar items in DB
        similar = [k for k in db_items if item.replace(' ', '_') in k or k.startswith(item.split()[0])]
        if similar:
            print(f'  Similar in DB: {similar[:5]}')

print('\n\n' + '=' * 80)
print(f'BROKEN ALIASES: {len(broken)}')
for alias, target in broken:
    print(f'  ❌ {alias} -> {target}')
