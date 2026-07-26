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
