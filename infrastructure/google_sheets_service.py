from datetime import date


def _build_google_sheets_client(secrets, gspread_module, credentials_cls):
    if gspread_module is None or credentials_cls is None:
        return None, None, "Google Sheets libraries are not installed. Add gspread and google-auth dependencies."

    sheet_cfg = secrets.get("google_sheet", {})
    spreadsheet_id = sheet_cfg.get("spreadsheet_id", secrets.get("GOOGLE_SHEET_ID", ""))
    worksheet_name = sheet_cfg.get("worksheet", secrets.get("GOOGLE_SHEET_WORKSHEET", "Sheet1"))
    creds_info = secrets.get("gcp_service_account", sheet_cfg.get("service_account", None))

    if not spreadsheet_id:
        return None, None, "Google Sheet ID is missing. Configure it in Streamlit secrets."

    if not creds_info:
        return None, None, "Service account credentials are missing. Configure gcp_service_account in Streamlit secrets."

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

        return worksheet, worksheet_name, ""
    except Exception as err:
        return None, None, f"Google Sheet connection failed: {err}"


def _serialize_rows_for_headers(rows, headers):
    serialized = []
    for row in rows:
        row_values = []
        for header in headers:
            row_values.append(str(row.get(header, "")))
        serialized.append(row_values)
    return serialized


def push_validated_items_to_google_sheet(
    df,
    secrets,
    gspread_module,
    credentials_cls,
    target_date=None,
    source_file="",
    replace_existing=False,
):
    """
    Push validated items to Google Sheets with Order column to preserve extraction sequence.
    Sheet Format: Order | Date | [original columns...]
    Args:
        target_date: ISO format date string (YYYY-MM-DD). If None, uses today's date.
    """
    if df is None or len(df) == 0:
        return False, "No validated rows to push."

    worksheet, worksheet_name, conn_err = _build_google_sheets_client(
        secrets,
        gspread_module,
        credentials_cls,
    )
    if worksheet is None:
        return False, conn_err

    try:
        push_df = df.copy()
        # Add Order column (1-based sequence) as first column
        push_df.insert(0, "Order", range(1, len(push_df) + 1))
        # Add Date column (use target_date if provided, otherwise today)
        push_df["Date"] = target_date if target_date else date.today().isoformat()
        push_df["Source File"] = str(source_file or "")
        push_df = push_df.fillna("")
        
        # Reorder columns to put Order and Date first
        cols = push_df.columns.tolist()
        # Move Order to first, Date to second
        cols.remove("Order")
        cols.remove("Date")
        cols.remove("Source File")
        push_df = push_df[["Order", "Date", "Source File"] + cols]

        headers = [str(col) for col in push_df.columns]
        values = push_df.astype(str).values.tolist()

        existing_header = worksheet.row_values(1)
        if not existing_header:
            worksheet.append_row(headers, value_input_option="USER_ENTERED")
            existing_header = headers.copy()

        if not replace_existing:
            worksheet.append_rows(values, value_input_option="USER_ENTERED")
            return True, f"Pushed {len(values)} row(s) to Google Sheet ({worksheet_name})."

        all_values = worksheet.get_all_values()
        existing_rows = []
        for raw_row in all_values[1:]:
            row_map = {}
            for idx, col_name in enumerate(existing_header):
                row_map[col_name] = raw_row[idx] if idx < len(raw_row) else ""
            existing_rows.append(row_map)

        target_date_str = target_date if target_date else date.today().isoformat()
        source_file_str = str(source_file or "")

        filtered_rows = []
        removed_count = 0
        for row in existing_rows:
            if row.get("Date", "").strip() == target_date_str and row.get("Source File", "").strip() == source_file_str:
                removed_count += 1
                continue
            filtered_rows.append(row)

        incoming_rows = []
        for row_values in values:
            row_map = {}
            for idx, col_name in enumerate(headers):
                row_map[col_name] = row_values[idx] if idx < len(row_values) else ""
            incoming_rows.append(row_map)

        final_headers = list(existing_header)
        if "Date" not in final_headers:
            final_headers.append("Date")
        if "Source File" not in final_headers:
            final_headers.append("Source File")
        for col in headers:
            if col not in final_headers:
                final_headers.append(col)

        merged_rows = filtered_rows + incoming_rows
        body = _serialize_rows_for_headers(merged_rows, final_headers)

        worksheet.clear()
        worksheet.update("A1", [final_headers], value_input_option="USER_ENTERED")
        if body:
            worksheet.update("A2", body, value_input_option="USER_ENTERED")

        return True, (
            f"Synced {len(values)} row(s) to Google Sheet ({worksheet_name}) "
            f"for source '{source_file_str}' on {target_date_str} "
            f"(replaced {removed_count} row(s))."
        )
    except Exception as err:
        return False, f"Google Sheet push failed: {err}"


def remove_validated_items_from_google_sheet(
    target_date,
    source_file,
    secrets,
    gspread_module,
    credentials_cls,
):
    worksheet, worksheet_name, conn_err = _build_google_sheets_client(
        secrets,
        gspread_module,
        credentials_cls,
    )
    if worksheet is None:
        return False, conn_err

    try:
        header = worksheet.row_values(1)
        if not header:
            return True, "Google Sheet is empty. Nothing to remove."

        if "Date" not in header or "Source File" not in header:
            return False, (
                "Sheet removal needs 'Date' and 'Source File' columns in row 1. "
                "Cannot safely remove upload-specific rows without them."
            )

        all_values = worksheet.get_all_values()
        existing_rows = []
        for raw_row in all_values[1:]:
            row_map = {}
            for idx, col_name in enumerate(header):
                row_map[col_name] = raw_row[idx] if idx < len(raw_row) else ""
            existing_rows.append(row_map)

        kept_rows = []
        removed_count = 0
        target_date_str = str(target_date or "").strip()
        source_file_str = str(source_file or "").strip()

        for row in existing_rows:
            if row.get("Date", "").strip() == target_date_str and row.get("Source File", "").strip() == source_file_str:
                removed_count += 1
                continue
            kept_rows.append(row)

        if removed_count == 0:
            return True, (
                f"No Google Sheet rows found for source '{source_file_str}' on {target_date_str}."
            )

        worksheet.clear()
        worksheet.update("A1", [header], value_input_option="USER_ENTERED")

        if kept_rows:
            worksheet.update(
                "A2",
                _serialize_rows_for_headers(kept_rows, header),
                value_input_option="USER_ENTERED",
            )

        return True, (
            f"Removed {removed_count} Google Sheet row(s) "
            f"for source '{source_file_str}' on {target_date_str} from {worksheet_name}."
        )
    except Exception as err:
        return False, f"Google Sheet removal failed: {err}"


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
