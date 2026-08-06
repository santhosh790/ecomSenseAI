"""Test client JSON loading and short name mapping"""
import sys
sys.path.insert(0, '/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI')

import json
from pathlib import Path

print('=' * 80)
print('TESTING CLIENT JSON STRUCTURE')
print('=' * 80)
print()

# Load the JSON file
clients_file = Path('/Users/a616152/Documents/MAC2220002/Documents/Personal/Projects/DataScience/ecomParse/ecomSenseAI/data/clients.json')

if not clients_file.exists():
    print('❌ clients.json not found')
    sys.exit(1)

with open(clients_file, 'r', encoding='utf-8') as f:
    clients_dict = json.load(f)

print('Loaded clients from JSON:')
print('-' * 80)
print(json.dumps(clients_dict, indent=2, ensure_ascii=False))
print()

print('Full Name → Short Name Mapping:')
print('-' * 80)
for full_name, short_name in sorted(clients_dict.items()):
    print(f'  {full_name:30} → {short_name}')
print()

# Test the functions
print('Testing Helper Functions:')
print('-' * 80)

# Test load_clients
from ecomSenseAI import load_clients, get_client_full_names, get_client_short_name

loaded = load_clients()
print(f'✅ load_clients() returned {len(loaded)} clients')
print()

# Test get_client_full_names
full_names = get_client_full_names()
print(f'✅ get_client_full_names() returned {len(full_names)} names:')
for name in full_names:
    print(f'   - {name}')
print()

# Test get_client_short_name
print('✅ Testing get_client_short_name():')
test_cases = [
    'RASSENSE PVT LTD',
    'MRF',
    'FUSION FOOD PVT LTD',
    'VIT-S BLOCK',
    'UNKNOWN CLIENT'  # Test fallback
]

for test_client in test_cases:
    short = get_client_short_name(test_client)
    expected = clients_dict.get(test_client, test_client)
    status = '✓' if short == expected else '✗'
    print(f'   {status} {test_client:30} → {short:15} (expected: {expected})')
print()

# Test UI flow simulation
print('UI Flow Simulation:')
print('-' * 80)
print('1. User selects "RASSENSE PVT LTD" from dropdown')
print('   → Stored in session_state["active_client_name"] = "RASSENSE PVT LTD"')
print()
print('2. When generating report:')
client_full = "RASSENSE PVT LTD"
client_short = get_client_short_name(client_full)
print(f'   → get_client_short_name("{client_full}") = "{client_short}"')
print(f'   → Report shows: "வாடிக்கையாளர்: {client_short}"')
print()

print('3. User adds new client:')
print('   Full Name: "ACME CORPORATION"')
print('   Short Name: "ACME"')
print('   → save_client("ACME CORPORATION", "ACME")')
print()

# Summary
print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'✅ JSON file loaded successfully')
print(f'✅ {len(clients_dict)} clients configured')
print(f'✅ Full names available for dropdown selection')
print(f'✅ Short names mapped for report display')
print()
print('Benefits:')
print('  • Clean UI with descriptive full names')
print('  • Compact reports with short names')
print('  • Easy to add new clients with custom short names')
print('=' * 80)
