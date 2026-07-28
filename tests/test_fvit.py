"""
Test FVIT client extraction with complete real data.
"""

from application.extraction_service import detect_vegetables
from application.vegetable_catalog_service import load_vegetable_catalog

# Complete FVIT PDF text (provided by user)
fvit_pdf_text = """Purchase Order
Vendor Code
405485
Vendor Name
PKS FRESH
Vendor Address
PKS FRESH, VELLORE, N0.19/1
SARATHY MANSION
Vendor Contact no
Vendor GST no
Vendor FSSAI no
Vendor Email id
pksfresh1@gmail.com
PO Number
8110170328
PO Date
27.07.2026
PO Delivery date
28.07.2026
PO Type
ZFPO
Purchase group
CR1
Delivery address
VELLORE INSTITUTE OF TECHNOLOGY,
VIT Campus, Katpadi Taluk,, 1, VIT University
Vellore,, Vellore, 632014
S.N
o
Material
Code
Description
HSN/SAC UO
M
Quantity
Price per
UOM
SGST
%
CGST
%
IGST
%
GST
Amount
Total Net
Amount
10
206607
ONION
BIG_UB_1X1KG
07122000 KG 150.000
31.00
0
0
0 
4,650 
20
206610
POTATO
LARGE_UB_1X1
KG
07122000 KG 100.000
20.00
0
0
0 
2,000 
30
206627
TOMATO
COUNTRY_UB_1
X1KG
07122000 KG 175.000
21.00
0
0
0 
3,675 
40
206573
CARROT_UB_1X
1KG
07099990 KG 15.000
45.00
0
0
0 
675 
50
206585
FRENCH
BEANS_UB_1X1
KG
07093000 KG 8.000
60.00
0
0
0 
480 
60
206569
CABBAGE_UB_1
X1KG
07051100 KG 35.000
30.00
0
0
0 
1,050 
70
206574
CAULIFLOWER_
UB_1X1KG
07051100 KG 45.000
36.00
0
0
0 
1,620 
80
206570
CAPSICUM
GREEN_UB_1X1
KG
07070000 KG 10.000
35.00
0
0
0 
350 
90
206586
GINGER
FRESH_UB_1X1
KG
08055000 KG 8.000
115.00
0
0
0 
920 
100
206589
GREEN
CHILLY_UB_1X1
KG
08055000 KG 6.000
35.00
0
0
0 
210 
110
206581
CUCUMBER
MALABAR_UB_1
X1KG
07070000 KG 100.000
20.00
0
0
0 
2,000 
120
206599
LEMON_UB_1X1
KG
08055000 KG 3.000
65.00
0
0
0 
195 
130
206583
CURRY
LEAVES_UB_1X1
KG
07099990 KG 1.000
25.00
0
0
0 
25 
140
206579
CORIANDER
LEAVES_UB_1X1
KG
07099990 KG 7.000
50.00
0
0
0 
350 
150
206605
MINT
LEAVES_UB_1X1
KG
07099990 KG 1.000
30.00
0
0
0 
30 
Gross Amount (INR):
0.000 
23,737.00 
Rassense Private Limited, Plot No 15/16/17, Vision Tower, Yogam Garden, Brindhavan Nagar Main Road, Valasaravakkam, Chennai, Tamil Nadu, 600087.
GSTIN NO: 33AAMCR8281K1ZS
Purchase Order
S.N
o
Material
Code
Description
HSN/SAC UO
M
Quantity
Price per
UOM
SGST
%
CGST
%
IGST
%
GST
Amount
Total Net
Amount
160
206930
SPRING
ONION_UB_1X1
NOS
07099990 EA 10.000
10.00
0
0
0.00 
100.000 
170
206929
PALAK_UB_1X1K
G
07099990 KG 15.000
35.00
0
0
0 
525 
180
206625
TENDIL_UB_1X1
KG
08039010 KG 25.000
30.00
0
0
0 
750 
190
206606
MUSHROOM
BUTTON
FRESH_UB_1X1
KG
07104000_
A
KG 20.000
200.00
0
0
0 
4,000 
200
206611
RADISH
WHITE_UB_1X1K
G
08039010 KG 6.000
22.00
0
0
0 
132 
Gross Amount (INR):
0.000 
23,737.00 
"""

catalog = load_vegetable_catalog()

print("=" * 80)
print("FVIT Client - Complete Extraction Test")
print("=" * 80)

results, report = detect_vegetables(
    text=fvit_pdf_text,
    vegetable_aliases=catalog.vegetable_aliases,
    vegetable_tamil_map=catalog.vegetable_tamil_map,
    noise_line_patterns=catalog.noise_line_patterns,
    return_details=True,
    confidence_threshold=75,
    client_name="FVIT"
)

print(f"\n📊 Extraction Report:")
print(f"  Client Name: FVIT")
print(f"  Parser Strategy: {report.get('parser_strategy', 'N/A')}")
print(f"  VIT Mode Activated: {report.get('vit_mode_activated', False)}")
print(f"  VIT Activation Reason: {report.get('vit_activation_reason', 'N/A')}")
print(f"  Candidates Found: {report.get('candidate_lines', 0)}")
print(f"  Extracted Rows: {report.get('extracted_rows', 0)}")
print(f"  With Quantity: {report.get('with_quantity', 0)}")
print(f"  High Confidence (≥90%): {report.get('high_confidence', 0)}")

print(f"\n✅ Successfully Extracted ({len(results)} items):")
print("-" * 80)
for item in results:
    print(f"  {item['Source Name']:25} | {item['Quantity']:15} | {item['Confidence']:3}% | {item['Status']}")

expected = ["Onion", "Potato", "Tomato", "Carrot", "Beans French", "Cabbage", "Cauliflower", 
            "Capsicum", "Ginger", "Green Chilly", "Cucumber", "Lemon", "Curry Leaves", 
            "Coriander", "Mint", "Spring Onion", "Spinach", "Tendli", "Mushroom", "Radish"]

print(f"\n📋 Validation:")
print(f"  Expected: {len(expected)} items")
print(f"  Extracted: {len(results)} items")
print(f"  All with quantities: {'✅ Yes' if all(item['Quantity'] for item in results) else '❌ No'}")
print(f"  Match: {'✅ PERFECT!' if len(results) == len(expected) else '⚠️ Mismatch'}")

if len(results) == len(expected) and all(item['Quantity'] for item in results):
    print("\n🎉 FVIT extraction working perfectly!")
    print("   Format is identical to VIT - using same VIT parser successfully.")
else:
    print(f"\n⚠️  Issues detected")

print("\n" + "=" * 80)

