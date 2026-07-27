from datetime import date


def push_validated_items_to_google_sheet(
    df,
    secrets,
    gspread_module,
    credentials_cls,
):
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
        push_df["Date"] = date.today().isoformat()
        push_df = push_df.fillna("")

        headers = [str(col) for col in push_df.columns]
        values = push_df.astype(str).values.tolist()

        existing_header = worksheet.row_values(1)
        if not existing_header:
            worksheet.append_row(headers, value_input_option="USER_ENTERED")

        worksheet.append_rows(values, value_input_option="USER_ENTERED")

        return True, f"Pushed {len(values)} row(s) to Google Sheet."
    except Exception as err:
        return False, f"Google Sheet push failed: {err}"
