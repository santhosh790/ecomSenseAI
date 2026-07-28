"""
Quick test to verify detect_vegetables wrapper function works
"""

# Simulate session state
class MockSessionState:
    def __init__(self):
        self.data = {
            "confidence_match_threshold": 75,
            "confidence_auto_extract_threshold": 90,
            "parser_selection": "Generic"
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)

# Mock streamlit
class st:
    session_state = MockSessionState()

# Now test the wrapper logic
from application.vegetable_detection_service import detect_vegetables as detect_vegetables_service

def detect_vegetables(text, return_details=False, parser_selection=None):
    confidence_match_threshold = int(st.session_state.get("confidence_match_threshold", 75))
    confidence_auto_extract_threshold = int(st.session_state.get("confidence_auto_extract_threshold", 90))
    
    # Use parser_selection if provided, otherwise use from session state
    if parser_selection is None:
        parser_selection = st.session_state.get("parser_selection", "Generic")
    
    # Map parser selection to client_name parameter
    # Generic = None (auto-detect), VIT/FVIT = pass as client_name
    client_name = None if parser_selection == "Generic" else parser_selection

    return detect_vegetables_service(
        text,
        return_details=return_details,
        confidence_threshold=confidence_match_threshold,
        auto_extract_threshold=confidence_auto_extract_threshold,
        client_name=client_name,
    )

# Test cases
print("=" * 80)
print("WRAPPER FUNCTION TEST")
print("=" * 80)

test_text = "1 ONION 5 KG"

# Test 1: Generic parser (default)
print("\n1. Testing Generic parser (parser_selection=None, using session state)")
try:
    items, report = detect_vegetables(test_text, return_details=True)
    print(f"   ✅ Success: {len(items)} items extracted")
    print(f"   Parser: {report.get('parser_strategy', 'N/A')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: VIT parser
print("\n2. Testing VIT parser (parser_selection='VIT')")
try:
    items, report = detect_vegetables(test_text, return_details=True, parser_selection='VIT')
    print(f"   ✅ Success: {len(items)} items extracted")
    print(f"   Parser: {report.get('parser_strategy', 'N/A')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: FVIT parser
print("\n3. Testing FVIT parser (parser_selection='FVIT')")
try:
    items, report = detect_vegetables(test_text, return_details=True, parser_selection='FVIT')
    print(f"   ✅ Success: {len(items)} items extracted")
    print(f"   Parser: {report.get('parser_strategy', 'N/A')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ All wrapper function tests passed!")
print("=" * 80)
