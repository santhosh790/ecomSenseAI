"""
Test script to verify VIT-specific extraction from the provided PDF.
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

# Load vegetable catalog
catalog = load_vegetable_catalog()

# VIT PDF sample text - extracted from the attached PDF
vit_pdf_text = """Purchase Order
Vendor Code 405485
Vendor Name PKS FRESH
Vendor Address PKS FRESH, VELLORE, N0.19/1 SARATHY MANSION
Vendor Contact no
Vendor GST no
Vendor FSSAI no
Vendor Email id pksfresh1@gmail.com
PO Number 8110170328
PO Date 27.07.2026
PO Delivery date 28.07.2026
PO Type ZFPO
Purchase group CR1
Delivery address VELLORE INSTITUTE OF TECHNOLOGY, VIT Campus, Katpadi Taluk,, 1, VIT University Vellore,, Vellore, 632014
S.No Material Code Description HSN/SAC UOM Quantity Price per UOM SGST % CGST % IGST % GST Amount Total Net Amount
10 206607 ONION BIG_UB_1X1KG 07122000 KG 150.000 31.00 0 0 0 4,650
20 206610 POTATO LARGE_UB_1X1 KG 07122000 KG 100.000 20.00 0 0 0 2,000
30 206627 TOMATO COUNTRY_UB_1 X1KG 07122000 KG 175.000 21.00 0 0 0 3,675
40 206573 CARROT_UB_1X 1KG 07099990 KG 15.000 45.00 0 0 0 675
50 206585 FRENCH BEANS_UB_1X1 KG 07093000 KG 8.000 60.00 0 0 0 480
60 206569 CABBAGE_UB_1 X1KG 07051100 KG 35.000 30.00 0 0 0 1,050
70 206574 CAULIFLOWER_ UB_1X1KG 07051100 KG 45.000 36.00 0 0 0 1,620
80 206570 CAPSICUM GREEN_UB_1X1 KG 07070000 KG 10.000 35.00 0 0 0 350
90 206586 GINGER FRESH_UB_1X1 KG 08055000 KG 8.000 115.00 0 0 0 920
100 206589 GREEN CHILLY_UB_1X1 KG 08055000 KG 6.000 35.00 0 0 0 210
110 206581 CUCUMBER MALABAR_UB_1 X1KG 07070000 KG 100.000 20.00 0 0 0 2,000
120 206599 LEMON_UB_1X1 KG 08055000 KG 3.000 65.00 0 0 0 195
130 206583 CURRY LEAVES_UB_1X1 KG 07099990 KG 1.000 25.00 0 0 0 25
140 206579 CORIANDER LEAVES_UB_1X1 KG 07099990 KG 7.000 50.00 0 0 0 350
150 206605 MINT LEAVES_UB_1X1 KG 07099990 KG 1.000 30.00 0 0 0 30
160 206930 SPRING ONION_UB_1X1 NOS 07099990 EA 10.000 10.00 0 0 0.00 100.000
170 206929 PALAK_UB_1X1K G 07099990 KG 15.000 35.00 0 0 0 525
180 206625 TENDIL_UB_1X1 KG 08039010 KG 25.000 30.00 0 0 0 750
190 206606 MUSHROOM BUTTON FRESH_UB_1X1 KG 07104000_ A KG 20.000 200.00 0 0 0 4,000
200 206611 RADISH WHITE_UB_1X1K G 08039010 KG 6.000 22.00 0 0 0 132
Gross Amount (INR): 0.000 23,737.00
"""

# Test with client_name="VIT" to force VIT mode
print("=" * 80)
print("Testing VIT Extraction with client_name='VIT'")
print("=" * 80)

results, report = detect_vegetables(
    text=vit_pdf_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    confidence_threshold=75,
    client_name="VIT"  # Force VIT mode
)

print(f"\n📊 Extraction Report:")
print(f"  Parser Strategy: {report.get('parser_strategy', 'N/A')}")
print(f"  VIT Mode Activated: {report.get('vit_mode_activated', False)}")
print(f"  VIT Activation Reason: {report.get('vit_activation_reason', 'N/A')}")
print(f"  VIT Extraction Attempted: {report.get('vit_extraction_attempted', False)}")
print(f"  VIT Extraction Found Rows: {report.get('vit_extraction_found_rows', False)}")
print(f"  Parser Fallback: {report.get('parser_fallback', False)}")
print(f"  Total Lines: {report.get('total_lines', 0)}")
print(f"  Candidate Lines: {report.get('candidate_lines', 0)}")
print(f"  Extracted Rows: {report.get('extracted_rows', 0)}")
print(f"  With Quantity: {report.get('with_quantity', 0)}")
print(f"  High Confidence (≥90%): {report.get('high_confidence', 0)}")

print(f"\n✅ Successfully Extracted Items ({len(results)}):")
print("-" * 80)
for item in results:
    print(f"  {item['Source Name']:25} | {item['Quantity']:15} | Confidence: {item['Confidence']:3}% | Status: {item['Status']}")

if report.get('unmatched_lines'):
    print(f"\n❌ Unmatched Lines ({len(report['unmatched_lines'])}):")
    print("-" * 80)
    for line in report['unmatched_lines'][:10]:  # Show first 10
        print(f"  Line {line['Line']}: {line['Text'][:70]}")

# Verify expected items are extracted
print("\n" + "=" * 80)
print("Verification:")
print("=" * 80)

expected_items = {
    "Onion": "150 KG",
    "Potato": "100 KG",
    "Tomato": "175 KG",
    "Carrot": "15 KG",
    "Cabbage": "35 KG",
    "Ginger": "8 KG",
    "Spring Onion": "10 EA",
}

for veg_name, expected_qty in expected_items.items():
    found = [r for r in results if r['Source Name'].lower() == veg_name.lower()]
    if found:
        actual_qty = found[0]['Quantity']
        match = "✅" if actual_qty == expected_qty else "⚠️"
        print(f"{match} {veg_name:20} Expected: {expected_qty:10} | Got: {actual_qty:10}")
    else:
        print(f"❌ {veg_name:20} Expected: {expected_qty:10} | NOT FOUND")

print("\n" + "=" * 80)
print(f"Test completed! Extracted {len(results)} items from VIT PDF")
print("=" * 80)
