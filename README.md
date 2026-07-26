# ecomSenseAI
Automated extraction of vegetable items and quantities from PDF, image, and Excel documents.

## OCR dependency note

Image OCR needs both:
- Python package `pytesseract` (already in `requirements.txt`)
- System binary `tesseract` (must be installed on host)

### Local setup (macOS)

```bash
brew install tesseract
```

### Streamlit Cloud setup

Add a `packages.txt` file at repo root with:

```txt
tesseract-ocr
tesseract-ocr-eng
fonts-noto-core
fonts-lohit-taml
```

Without the system binary, image uploads will show a warning and OCR text extraction will be skipped.

## Tamil font on Streamlit Cloud

Tamil text in PDF export is rendered server-side via WeasyPrint. Streamlit Cloud does not include macOS fonts (like Tamil Sangam MN), so Linux fonts must be installed via `packages.txt`.

This repo now installs:
- `fonts-noto-core`
- `fonts-lohit-taml`

After pushing to GitHub, trigger a full app reboot/redeploy in Streamlit Cloud so apt packages are reinstalled.

## Push confirmed list to Google Sheets

After clicking `✅ Confirm`, validated rows are always appended to a dated CSV file in `outputs/` with an extra `Date` column.

Google Sheets push is optional and can be enabled from the app checkbox (`Also push confirmed rows to Google Sheet`).

### Validation workflow

- Upload files one by one.
- Validate rows and click `✅ Confirm` to save.
- Saved rows are stored in `outputs/validated_YYYY-MM-DD.csv` with `Source File`, `Date`, and `Saved At`.
- Revalidating the same file updates (replaces) that file's rows in today's CSV.
- Consolidated output now sums quantities across all saved files for the current date.

### Date-based views

- Individual order view by selected date and file.
- Consolidated order by selected date.
- Updating a saved file immediately refreshes consolidation for that date.
- For today's saved image uploads, the original uploaded image is shown during revalidation.

### App navigation

- `Primary Flow`: Upload -> Extract -> Validate -> Confirm -> View and download confirmed output.
- `Saved Orders`: Select saved date/file -> Revalidate/update -> Download individual order.
- `Consolidated Orders`: Select date -> View/download consolidated quantities across files.

### Streamlit secrets configuration

In Streamlit Cloud, set these secrets:

```toml
[google_sheet]
spreadsheet_id = "YOUR_SPREADSHEET_ID"
worksheet = "Sheet1"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

Also share the target Google Sheet with the `client_email` from the service account as Editor.
