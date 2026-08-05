from datetime import date


def push_validated_items_to_google_sheet(
    df,
    secrets,
    gspread_module,
    credentials_cls,
    target_date=None,
):
    """
    Push validated items to Google Sheets with Order column to preserve extraction sequence.
    Sheet Format: Order | Date | [original columns...]
    Args:
        target_date: ISO format date string (YYYY-MM-DD). If None, uses today's date.
    """
    if df is None or len(df) == 0:
        return False, "No validated rows to push."

    if gspread_module is None or credentials_cls is None:
        return False, "Google Sheets libraries are not installed. Add gspread and google-auth dependencies."

    sheet_cfg = secrets.get("google_sheet", {})
    spreadsheet_id = sheet_cfg.get("spreadsheet_id", secrets.get("GOOGLE_SHEET_ID", ""))
    worksheet_name = sheet_cfg.get("worksheet", secrets.get("GOOGLE_SHEET_WORKSHEET", "Sheet1"))
    creds_info = secrets.get("gcp_service_account", sheet_cfg.get("service_account", None))

    if not spreadsheet_id:
        return False, "Google Sheet ID is missing. Configure it in Streamlit secrets."

    if not creds_info:
        return False, "Service account credentials are missing. Configure gcp_service_account in Streamlit secrets."

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds = credentials_cls.from_service_account_info(dict(creds_info), scopes=scopes)
        client = gspread_module.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread_module.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)

        push_df = df.copy()
        # Add Order column (1-based sequence) as first column
        push_df.insert(0, "Order", range(1, len(push_df) + 1))
        # Add Date column (use target_date if provided, otherwise today)
        push_df["Date"] = target_date if target_date else date.today().isoformat()
        push_df = push_df.fillna("")
        
        # Reorder columns to put Order and Date first
        cols = push_df.columns.tolist()
        # Move Order to first, Date to second
        cols.remove("Order")
        cols.remove("Date")
        push_df = push_df[["Order", "Date"] + cols]

        headers = [str(col) for col in push_df.columns]
        values = push_df.astype(str).values.tolist()

        existing_header = worksheet.row_values(1)
        if not existing_header:
            worksheet.append_row(headers, value_input_option="USER_ENTERED")

        worksheet.append_rows(values, value_input_option="USER_ENTERED")

        return True, f"Pushed {len(values)} row(s) to Google Sheet."
    except Exception as err:
        return False, f"Google Sheet push failed: {err}"


def push_consolidated_to_google_sheet(
    df,
    target_date,
    client_names,
    secrets,
    gspread_module,
    credentials_cls,
):
    """
    Push consolidated data to Google Sheets with upsert logic based on primary key.
    Transforms wide format (client columns) to long format (one row per client per item).
    Primary Key: Date + ClientName + Item
    Sheet Format: Order | Date | ClientName | Item | Unit | Quantity
    Order column preserves the original extraction sequence to maintain item ordering.
    """
    if df is None or len(df) == 0:
        return False, "No consolidated rows to push."

    if gspread_module is None or credentials_cls is None:
        return False, "Google Sheets libraries are not installed. Add gspread and google-auth dependencies."

    sheet_cfg = secrets.get("google_sheet", {})
    spreadsheet_id = sheet_cfg.get("spreadsheet_id", secrets.get("GOOGLE_SHEET_ID", ""))
    creds_info = secrets.get("gcp_service_account", sheet_cfg.get("service_account", None))

    if not spreadsheet_id:
        return False, "Google Sheet ID is missing. Configure it in Streamlit secrets."

    if not creds_info:
        return False, "Service account credentials are missing. Configure gcp_service_account in Streamlit secrets."

    try:
        import pandas as pd
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds = credentials_cls.from_service_account_info(dict(creds_info), scopes=scopes)
        client = gspread_module.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Use "consolidated" worksheet
        worksheet_name = "consolidated"
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread_module.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)

        # Transform data from wide to long format
        # Identify client columns (exclude Tamil Name, Total Quantity, Unit)
        base_cols = ["Tamil Name", "Total Quantity", "Unit"]
        client_cols = [col for col in df.columns if col not in base_cols]
        
        if not client_cols:
            return False, "No client columns found in consolidated data."
        
        # Prepare long format data with order preservation
        long_format_rows = []
        
        for item_order, (_, row) in enumerate(df.iterrows(), start=1):
            tamil_name = str(row.get("Tamil Name", "")).strip()
            unit = str(row.get("Unit", "")).strip()
            
            # Create one row per client with non-zero quantity
            for client_col in client_cols:
                quantity = row.get(client_col, 0)
                
                # Convert quantity to float, skip if 0 or empty
                try:
                    qty_float = float(quantity) if quantity != "" else 0.0
                    if qty_float == 0.0:
                        continue  # Skip zero quantities
                except (ValueError, TypeError):
                    continue
                
                # Add row: Order, Date, ClientName, Item, Unit, Quantity
                long_format_rows.append({
                    "Order": item_order,
                    "Date": target_date,
                    "ClientName": client_col,
                    "Item": tamil_name,
                    "Unit": unit,
                    "Quantity": qty_float
                })
        
        if not long_format_rows:
            return False, "No non-zero quantities found to push."
        
        # Create DataFrame with correct column order (Order first)
        push_df = pd.DataFrame(long_format_rows)
        push_df = push_df[["Order", "Date", "ClientName", "Item", "Unit", "Quantity"]]
        push_df = push_df.fillna("")
        
        headers = ["Order", "Date", "ClientName", "Item", "Unit", "Quantity"]
        
        # Get existing data from sheet
        existing_header = worksheet.row_values(1)
        if not existing_header:
            # Empty sheet - add header and all rows
            worksheet.append_row(headers, value_input_option="USER_ENTERED")
            values = push_df.astype(str).values.tolist()
            worksheet.append_rows(values, value_input_option="USER_ENTERED")
            return True, f"Initialized consolidated sheet with {len(values)} row(s)."
        
        # Ensure headers match
        if existing_header != headers:
            return False, f"Sheet headers don't match. Expected {headers}, found {existing_header}."
        
        # Get all existing data
        all_data = worksheet.get_all_values()
        existing_rows = all_data[1:]  # Skip header
        
        # Build a lookup dictionary: (Date, ClientName, Item) -> (row_index, current_data)
        primary_key_lookup = {}
        for idx, row in enumerate(existing_rows, start=2):  # Row 2 is first data row (1 is header)
            if len(row) >= 4:  # Need at least Order, Date, ClientName, Item
                # Columns: Order(0), Date(1), ClientName(2), Item(3), Unit(4), Quantity(5)
                date_val = row[1].strip()
                client_val = row[2].strip()
                item_val = row[3].strip()
                key = (date_val, client_val, item_val)
                primary_key_lookup[key] = (idx, row)
        
        # Process each row in the push dataframe
        # Collect updates and inserts separately for batch operations
        rows_to_update = []  # List of (range, values) tuples
        rows_to_insert = []
        
        for _, row_data in push_df.iterrows():
            date_val = str(row_data["Date"]).strip()
            client_val = str(row_data["ClientName"]).strip()
            item_val = str(row_data["Item"]).strip()
            key = (date_val, client_val, item_val)
            
            row_values = [str(val) for val in row_data.values]
            
            if key in primary_key_lookup:
                # Collect row update
                row_idx, existing_row = primary_key_lookup[key]
                # Create range string like "A2:F2" (Order, Date, ClientName, Item, Unit, Quantity)
                range_str = f"A{row_idx}:F{row_idx}"
                rows_to_update.append({
                    'range': range_str,
                    'values': [row_values]
                })
            else:
                # Collect new row to insert
                rows_to_insert.append(row_values)
        
        # Perform batch update for existing rows (single API call)
        if rows_to_update:
            worksheet.batch_update(rows_to_update, value_input_option="USER_ENTERED")
        
        # Perform batch insert for new rows (single API call)
        if rows_to_insert:
            worksheet.append_rows(rows_to_insert, value_input_option="USER_ENTERED")
        
        summary = []
        if rows_to_update:
            summary.append(f"updated {len(rows_to_update)} row(s)")
        if rows_to_insert:
            summary.append(f"inserted {len(rows_to_insert)} row(s)")
        
        return True, f"Consolidated push complete: {', '.join(summary)}."
    except Exception as err:
        return False, f"Google Sheet consolidated push failed: {err}"
