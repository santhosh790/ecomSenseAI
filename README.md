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
```

Without the system binary, image uploads will show a warning and OCR text extraction will be skipped.
