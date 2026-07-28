# VIT/FVIT Extraction - Usage Guide

## ✅ What Was Implemented

The application now has **client-specific extraction** using raw text. VIT and FVIT documents get specialized parsing that reliably extracts vegetables and quantities with UOM.

## 🎯 Extraction Approach

**Client-Specific Raw Text Extraction:**
- All extraction uses raw text from PDFs/images
- No column mapping required - everything is automatic
- Client name determines which parser to use
- VIT/FVIT mode handles multi-line PDF format

## 📋 How to Use VIT/FVIT Extraction

### Step 1: Enter Client Name
In the Streamlit application, locate the **"Client Name"** field and enter:
```
VIT
```
or
```
FVIT
```
(Both trigger the same VIT parser - case-insensitive)

### Step 2: Upload Your PDF
Upload your VIT/FVIT Purchase Order PDF using the file uploader. The app will:
- Extract raw text from the PDF
- Display the extracted text automatically
- No manual column mapping needed

### Step 3: Extract Vegetables
Click the **"🔍 Extract Vegetables"** button to start extraction.

### Step 4: Verify VIT Mode is Active
After upload, you'll see an info box showing:
```
🔧 Parser: VIT-SPECIAL | VIT Mode: ✅ ACTIVATED (Client name: 'VIT')
```

### Step 5: Review Extracted Data
All 20 items should be extracted with:
- ✅ Correct vegetable names
- ✅ Quantities with UOM (KG/EA)
- ✅ 99% confidence scores
- ✅ Status: "Auto Extracted"

## 🎯 Expected Results

For the provided VIT PDF, you should see:
- **20 vegetables extracted** (100% success rate)
- **All with quantities and UOM** (150 KG, 10 EA, etc.)
- **High confidence (99%)** for all items
- **No unmatched lines**

## 🔍 Troubleshooting

### Issue: No quantities extracted
**Solution:** Make sure you entered "VIT" in the Client Name field

### Issue: VIT Mode shows "❌ Not Active"
**Check:**
1. Client Name field has "VIT" entered
2. Document is actually a VIT Purchase Order
3. Look for the helpful tip message suggesting to enter "VIT"

### Issue: Some items missing
**Solution:**
1. Check if vegetable aliases exist in `data/aliases.json`
2. Common mappings already added: PALAK → SPINACH, TENDIL → TENDLI

## 📊 What's Different in VIT Mode

**VIT Mode:**
- Uses specialized parser for VIT Purchase Order format
- Extracts from table structure: Serial | Item Code | Description | HSN | UOM | Quantity
- Handles multi-line descriptions
- Skips table headers automatically
- Normalizes quantities (removes trailing zeros)
- 99% confidence for successfully extracted items

**Generic Mode:**
- Uses pattern matching on text
- May miss quantities in structured tables
- Lower confidence scores
- More prone to extraction errors

## 🚀 Next Steps

Once VIT extraction is working:
1. Test with other VIT Purchase Orders
2. Add more client-specific extractors (coming soon)
3. Refine vegetable aliases as needed

## 📝 Technical Details

**Files Modified:**
- `application/extraction_service.py` - Added VIT extractor and improved parsing
- `ecomSenseAI.py` - Enhanced UI with client mode indicators
- `data/aliases.json` - Added PALAK and TENDIL mappings

**New Functions:**
- `extract_vit_row_fields()` - VIT-specific field extractor
- Enhanced `build_vit_row_candidates()` - Better header detection
- Improved fallback extraction logic
