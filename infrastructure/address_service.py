"""Address management service for delivery challans"""
import json
from pathlib import Path
from typing import Dict, List


ADDRESSES_FILE = Path(__file__).parent.parent / "data" / "addresses.json"


def load_addresses() -> Dict[str, List[Dict[str, str]]]:
    """Load saved addresses from JSON file."""
    if not ADDRESSES_FILE.exists():
        return {
            "bill_to_addresses": [],
            "ship_to_addresses": []
        }
    
    try:
        with open(ADDRESSES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading addresses: {e}")
        return {
            "bill_to_addresses": [],
            "ship_to_addresses": []
        }


def save_addresses(addresses_data: Dict[str, List[Dict[str, str]]]) -> bool:
    """Save addresses to JSON file."""
    try:
        with open(ADDRESSES_FILE, 'w', encoding='utf-8') as f:
            json.dump(addresses_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving addresses: {e}")
        return False


def add_bill_to_address(name: str, address: str) -> bool:
    """Add a new Bill To address."""
    addresses = load_addresses()
    
    # Check if already exists
    for addr in addresses["bill_to_addresses"]:
        if addr["name"].strip().upper() == name.strip().upper():
            return False  # Already exists
    
    addresses["bill_to_addresses"].append({
        "name": name.strip(),
        "address": address.strip()
    })
    
    return save_addresses(addresses)


def add_ship_to_address(name: str, address: str) -> bool:
    """Add a new Ship To address."""
    addresses = load_addresses()
    
    # Check if already exists
    for addr in addresses["ship_to_addresses"]:
        if addr["name"].strip().upper() == name.strip().upper():
            return False  # Already exists
    
    addresses["ship_to_addresses"].append({
        "name": name.strip(),
        "address": address.strip()
    })
    
    return save_addresses(addresses)


def get_bill_to_names() -> List[str]:
    """Get list of Bill To company names."""
    addresses = load_addresses()
    return [addr["name"] for addr in addresses["bill_to_addresses"]]


def get_ship_to_names() -> List[str]:
    """Get list of Ship To company names."""
    addresses = load_addresses()
    return [addr["name"] for addr in addresses["ship_to_addresses"]]


def get_bill_to_address(name: str) -> str:
    """Get Bill To address by company name."""
    addresses = load_addresses()
    for addr in addresses["bill_to_addresses"]:
        if addr["name"] == name:
            return addr["address"]
    return ""


def get_ship_to_address(name: str) -> str:
    """Get Ship To address by company name."""
    addresses = load_addresses()
    for addr in addresses["ship_to_addresses"]:
        if addr["name"] == name:
            return addr["address"]
    return ""
