"""
Date Selector UI Documentation
================================

LOCATION: Upload Order tab (before Client Name input)

UI LAYOUT:
----------

┌─────────────────────────────────────────────────────────────┐
│                      📤 Upload Order                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Upload PDF / Image / Excel                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Choose File                           No file chosen│    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Order Date  ⓘ                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  📅  08/05/2026                           ▼        │    │
│  └────────────────────────────────────────────────────┘    │
│  💡 Select the date for this order. You can upload          │
│     orders for different dates on the same day.             │
│                                                              │
│  Client Name  ⓘ                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Enter client name                                  │    │
│  └────────────────────────────────────────────────────┘    │
│  💡 Enter the actual client name (e.g., 'MRF',             │
│     'VIT Canteen'). Saved to CSV for record-keeping.       │
│                                                              │
│  Parser Strategy  ⓘ                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Generic                                    ▼       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘


FEATURES:
---------

1. **Date Picker Widget**
   - Type: st.date_input()
   - Default: Today's date
   - Allows: Any past or future date
   - Format: YYYY-MM-DD (ISO format internally)

2. **Multiple Orders Same Day**
   Example workflow on 2026-08-05:
   
   Upload #1:
   - Select date: 2026-08-04 (yesterday)
   - Upload: order_yesterday.pdf
   - Saves to: outputs/validated_2026-08-04.csv
   
   Upload #2:
   - Select date: 2026-08-05 (today)
   - Upload: order_today.pdf
   - Saves to: outputs/validated_2026-08-05.csv
   
   Upload #3:
   - Select date: 2026-08-06 (tomorrow)
   - Upload: order_tomorrow.pdf
   - Saves to: outputs/validated_2026-08-06.csv

3. **Data Flow**
   Selected Date → Session State (active_order_date)
                 ↓
   ┌─────────────┴─────────────┬─────────────────────┐
   ↓                           ↓                     ↓
   CSV File               Image Folder       Google Sheets
   validated_DATE.csv     uploads/DATE/      Date column


IMPLEMENTATION DETAILS:
-----------------------

Session State Key: active_order_date
Storage Format: datetime.date object
Passed As: .isoformat() → "YYYY-MM-DD" string

Functions Updated:
1. persist_uploaded_image(file, target_date)
   - Images saved to outputs/uploads/{target_date}/

2. save_validated_items_to_csv(df, ..., target_date)
   - CSV saved to outputs/validated_{target_date}.csv
   - Date column in CSV = target_date

3. push_validated_items_to_google_sheet(df, ..., target_date)
   - Date column in Sheet = target_date


USE CASES:
----------

✅ Backdating Orders
   - Received physical order yesterday
   - Enter it today with yesterday's date
   - Data correctly organized by order date

✅ Batch Processing
   - Process multiple orders from different dates
   - All on the same day
   - Each saved to correct date bucket

✅ Future Orders
   - Pre-enter orders for future dates
   - Useful for advance planning
   - Easy to locate by date later

✅ Corrections
   - Correct date on mistakenly entered order
   - Re-upload with correct date
   - Overwrites previous entry


BENEFITS:
---------

1. **Flexibility**: Not tied to today's date
2. **Organization**: Orders grouped by actual order date
3. **Batch Entry**: Process multiple dates in one session
4. **Accuracy**: Date reflects order date, not entry date
5. **Time Travel**: Can backdate or future-date as needed
"""

print(__doc__)
