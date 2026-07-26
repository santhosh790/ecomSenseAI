import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import io
import shutil
import base64
import mimetypes
from PIL import Image, ImageOps, ImageFilter
from datetime import date, datetime
from pathlib import Path

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

if pytesseract is not None:
    # Explicitly set binary path when available (helps on hosted runtimes).
    tesseract_binary = shutil.which("tesseract")
    if tesseract_binary:
        pytesseract.pytesseract.tesseract_cmd = tesseract_binary


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="eComSense AI",
    page_icon="🥕",
    layout="wide"
)


# ============================================================
# VEGETABLE MASTER DATA
# ============================================================

VEGETABLE_TAMIL_MAP = {
    "BABY CORN": "பேபி கார்ன்",
    "BANANA RAW": "வாழைக்காய்",
    "BANANA YELLAKKI": "வாழைப்பழம்",
    "BEANS FRENCH": "பிரெஞ்சு பீன்ஸ்",
    "BEANS CLUSTER": "கொத்தவரங்காய்",
    "BEETROOT": "பீட்ரூட்",
    "BRINJAL": "கத்திரிக்காய்",
    "BROCCOLI": "ப்ரோகோலி",
    "CABBAGE": "முட்டைக்கோஸ்",
    "CAPSICUM": "குடைமிளகாய்",
    "CARROT": "கேரட்",
    "CAULIFLOWER": "காலிஃப்ளவர்",
    "CHOW CHOW": "சௌ சௌ",
    "COCONUT": "தேங்காய்",
    "CORIANDER": "கொத்தமல்லி",
    "CUCUMBER": "வெள்ளரிக்காய்",
    "CURRY LEAVES": "கறிவேப்பிலை",
    "DRUMSTICK": "முருங்கைக்காய்",
    "GARLIC": "பூண்டு",
    "GINGER": "இஞ்சி",
    "GREEN CHILLY": "பச்சை மிளகாய்",
    "KEERA": "கீரை",
    "KNOL KHOL": "நூல்கோல்",
    "LADY FINGER": "வெண்டைக்காய்",
    "LAUKI": "சுரைக்காய்",
    "LEMON": "எலுமிச்சை",
    "MANGALORE CUCUMBER": "மங்களூர் வெள்ளரி",
    "MINT": "புதினா",
    "MUSHROOM": "காளான்",
    "MUSK MELON": "முலாம் பழம்",
    "MOSSAMBI": "சாத்துக்குடி",
    "ONION": "வெங்காயம்",
    "PAPAYA": "பப்பாளி",
    "PINEAPPLE": "அன்னாசி",
    "POTATO": "உருளைக்கிழங்கு",
    "PUMPKIN RED": "பரங்கிக்காய்",
    "PUMPKIN WHITE": "வெள்ளை பூசணிக்காய்",
    "RADISH": "முள்ளங்கி",
    "RAW MANGO": "மாங்காய்",
    "SNAKE GOURD": "புடலங்காய்",
    "SPINACH": "பசலை கீரை",
    "SPRING ONION": "ஸ்ப்ரிங் ஆனியன்",
    "TENDLI": "கோவைக்காய்",
    "TOMATO": "தக்காளி",
    "WATER MELON": "தர்பூசணி",
    "YAM SURAN": "சேனைக்கிழங்கு",
}

VEGETABLE_ALIASES = {
    "BABY CORN": "BABY CORN",
    "BANANA RAW": "BANANA RAW",
    "RAW BANANA": "BANANA RAW",
    "BANANA YELLAKKI": "BANANA YELLAKKI",
    "BEANS FRENCH": "BEANS FRENCH",
    "FRENCH BEANS": "BEANS FRENCH",
    "BEANS CLUSTER": "BEANS CLUSTER",
    "GAWAR": "BEANS CLUSTER",
    "BEETROOT": "BEETROOT",
    "BRINJAL BIG": "BRINJAL",
    "BRINJAL VARI": "BRINJAL",
    "BRINJAL": "BRINJAL",
    "BROCCOLI": "BROCCOLI",
    "CABBAGE GREEN": "CABBAGE",
    "CABBAGE": "CABBAGE",
    "CABAGE": "CABBAGE",
    "CAPSICUM GREEN": "CAPSICUM",
    "CAPSICUM": "CAPSICUM",
    "CARROT": "CARROT",
    "CAULIFLOWER": "CAULIFLOWER",
    "CHOW CHOW": "CHOW CHOW",
    "COCONUT RAW NOS": "COCONUT",
    "COCONUT FRESH": "COCONUT",
    "COCONUT": "COCONUT",
    "COCOUNT": "COCONUT",
    "RAW COCOUNT": "COCONUT",
    "CORIANDER FRESH": "CORIANDER",
    "CORIANDER LEAVES": "CORIANDER",
    "CORIANDER": "CORIANDER",
    "CORINDER": "CORIANDER",
    "CORINDER FRESH": "CORIANDER",
    "CUCUMBER": "CUCUMBER",
    "CURRY LEAVES": "CURRY LEAVES",
    "CURYLEAVE": "CURRY LEAVES",
    "CURYLEAVES": "CURRY LEAVES",
    "DRUM STICK": "DRUMSTICK",
    "DRUMSTICK": "DRUMSTICK",
    "GARLIC BOLD": "GARLIC",
    "GARLIC DRY": "GARLIC",
    "GARLIC": "GARLIC",
    "GINGER FRESH": "GINGER",
    "GINGER": "GINGER",
    "GREEN CHILLY": "GREEN CHILLY",
    "GREEN CHILLI": "GREEN CHILLY",
    "KEERA SOPPU": "KEERA",
    "SPINACH PALAK": "SPINACH",
    "SPINACH": "SPINACH",
    "KNOL KHOL": "KNOL KHOL",
    "LADY FINGER": "LADY FINGER",
    "LADIES FINGER": "LADY FINGER",
    "LAUKI": "LAUKI",
    "BOTTLE GOURD": "LAUKI",
    "LEMON YELLOW": "LEMON",
    "LEMON": "LEMON",
    "MANGALORE CUCUMBER": "MANGALORE CUCUMBER",
    "SOWTHEKAI": "MANGALORE CUCUMBER",
    "MINT FRESH": "MINT",
    "MINT LEAVES": "MINT",
    "MINT": "MINT",
    "MUSHROOM FRESH": "MUSHROOM",
    "MUSHROOM": "MUSHROOM",
    "MUSK MELON": "MUSK MELON",
    "MOSSAMBI": "MOSSAMBI",
    "SWEET LIME": "MOSSAMBI",
    "ONION BIG": "ONION",
    "ONION": "ONION",
    "PAPAYA": "PAPAYA",
    "PINEAPPLE": "PINEAPPLE",
    "POTATO LARGE": "POTATO",
    "POTATO": "POTATO",
    "POTOTO": "POTATO",
    "PUMPKIN RED": "PUMPKIN RED",
    "PUMPKIN WHITE": "PUMPKIN WHITE",
    "WHITE PUMPKIN": "PUMPKIN WHITE",
    "RADDISH": "RADISH",
    "RADISH": "RADISH",
    "RAW MANGO": "RAW MANGO",
    "SNAKE GOURD": "SNAKE GOURD",
    "SPRING ONION": "SPRING ONION",
    "TENDLI": "TENDLI",
    "TOMATO TABLE": "TOMATO",
    "TOMATO COUNTRY": "TOMATO",
    "TOMATO": "TOMATO",
    "WATER MELON": "WATER MELON",
    "YAM SURAN": "YAM SURAN",
}

NOISE_LINE_PATTERNS = [
    r"^purchase order",
    r"^order no",
    r"^delivery date",
    r"^payment terms",
    r"^department",
    r"^prepared by",
    r"^checked by",
    r"^authorised signatory",
    r"^amount \(in words\)",
    r"^total\s+\d",
    r"^cgst",
    r"^sgst",
    r"^igst",
    r"^page\s+\d",
]


# ============================================================
# SESSION INITIALIZATION
# ============================================================

if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""

if "items" not in st.session_state:
    st.session_state["items"] = []

if "validated_items" not in st.session_state:
    st.session_state["validated_items"] = []

if "extraction_report" not in st.session_state:
    st.session_state["extraction_report"] = {}

if "print_logo_data_uri" not in st.session_state:
    st.session_state["print_logo_data_uri"] = ""

if "push_gsheet_on_confirm" not in st.session_state:
    st.session_state["push_gsheet_on_confirm"] = False

if "active_source_file" not in st.session_state:
    st.session_state["active_source_file"] = ""

if "active_upload_type" not in st.session_state:
    st.session_state["active_upload_type"] = ""

if "active_uploaded_image_path" not in st.session_state:
    st.session_state["active_uploaded_image_path"] = ""

if "download_header_text" not in st.session_state:
    st.session_state["download_header_text"] = "PKS Fresh"

if "download_above_list_text" not in st.session_state:
    st.session_state["download_above_list_text"] = "காய்கறி பட்டியல்"

if "download_footer_text" not in st.session_state:
    st.session_state["download_footer_text"] = ""


# ============================================================
# DOCUMENT READERS
# ============================================================


def read_pdf(file):

    text = ""

    pdf = fitz.open(stream=file.read(), filetype="pdf")

    for page in pdf:
        text += page.get_text()

    return text



def read_excel(file):

    df = pd.read_excel(file)

    return df



def read_image(file):

    image = Image.open(file)

    return image


def extract_image_text(image):

    if pytesseract is None:
        return "", "pytesseract is not installed. Install pytesseract and Tesseract OCR engine to enable image extraction."

    # Improve OCR accuracy by converting to high-contrast grayscale.
    gray = ImageOps.grayscale(image)
    enhanced = ImageOps.autocontrast(gray)
    sharpened = enhanced.filter(ImageFilter.SHARPEN)

    try:
        text = pytesseract.image_to_string(sharpened)
    except pytesseract.pytesseract.TesseractNotFoundError:
        return (
            "",
            "Tesseract OCR binary is not installed on this system. "
            "For Streamlit Cloud, add a packages.txt with 'tesseract-ocr'. "
            "For macOS, run: brew install tesseract",
        )
    except pytesseract.pytesseract.TesseractError as err:
        return "", f"OCR failed: {err}"

    if not text.strip():
        return "", "No text detected in image. Try a clearer image or higher resolution scan."

    return text, ""



# ============================================================
# BASIC EXTRACTION LOGIC
# ============================================================


def extract_quantity(text):

    """
    Extract quantities like:
    2 kg
    500 gm
    1kg
    """

    pattern = r"(\d+\.?\d*)\s*(kg|kgs|g|gm|gram|grams)"

    matches = re.findall(
        pattern,
        text,
        flags=re.IGNORECASE
    )

    return matches


def normalize_text(text):

    normalized = re.sub(r"[^A-Za-z0-9]+", " ", str(text).upper())
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_material_name(name):

    value = normalize_text(name)

    # Remove packaging tokens that appear in table exports.
    value = re.sub(r"\bUB\b", " ", value)
    value = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", value)
    value = re.sub(r"\b\d+(?:\.\d+)?\s*(?:KG|KGS|NOS|EA)\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def is_noise_line(line):

    value = line.strip().lower()

    if not value:
        return True

    for pattern in NOISE_LINE_PATTERNS:
        if re.search(pattern, value):
            return True

    return False


def extract_row_quantity(text):

    compact = re.sub(r"\s+", " ", str(text)).strip().upper()
    compact = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", compact)
    compact = re.sub(r"\s+", " ", compact).strip()

    # Prefer table style first: "... KG 45 25.07.2026"
    unit_qty_match = re.search(
        r"\b(KG|KGS|NOS|EA)\.?\b\s*(\d+(?:\.\d+)?)\b",
        compact,
        flags=re.IGNORECASE,
    )

    if unit_qty_match:
        unit = unit_qty_match.group(1).upper()
        qty = unit_qty_match.group(2)
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return f"{qty} {unit}"

    # PO style: "... 1 Kgs 90.00 90.00"
    qty_unit_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(KG|KGS|G|GM|GRAMS?|NOS|EA)\.?\b",
        compact,
        flags=re.IGNORECASE,
    )

    if qty_unit_match:
        qty = qty_unit_match.group(1)
        unit = qty_unit_match.group(2).upper()
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return f"{qty} {unit}"

    return ""


def extract_row_fields(text):

    compact = re.sub(r"\s+", " ", str(text)).strip()
    compact = re.sub(r"\b\d+\s*X+\s*\d+\s*(?:K+G|KGS|NOS|EA)\b", " ", compact, flags=re.IGNORECASE)
    compact = re.sub(r"\s+", " ", compact).strip()

    # PO-style line: "1 1100006 BABY CORN PEELED 1 Kgs 90.00 90.00"
    po_match = re.search(
        r"^\s*\d+\s+\d{6,7}\s+(.+?)\s+(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\b",
        compact,
        flags=re.IGNORECASE,
    )

    if po_match:
        material = po_match.group(1).strip()
        qty = po_match.group(2)
        unit = po_match.group(3).upper()
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    # Table-style line: "1 206558 BEANS CLUSTER_UB_1X1KG KG 1"
    table_match = re.search(
        r"^\s*[\[\(\{\|_\-]*\s*\d+[\.)\]|_:\-]*\s+(?:\d+\s+)?(.+?)\s+(KG|KGS|NOS|EA)\.?\s+(\d+(?:\.\d+)?)\b",
        compact,
        flags=re.IGNORECASE,
    )

    if table_match:
        material = table_match.group(1).strip()
        unit = table_match.group(2).upper()
        qty = table_match.group(3)
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    # Free-form line: "Onion 80kg" or "Raw cocount 15nos"
    freeform_match = re.search(
        r"^\s*(.+?)\s+(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\.?\s*$",
        compact,
        flags=re.IGNORECASE,
    )

    if freeform_match:
        material = freeform_match.group(1).strip()
        qty = freeform_match.group(2)
        unit = freeform_match.group(3).upper()
        if unit in ["KG", "KGS"]:
            unit = "KG"
        return material, f"{qty} {unit}"

    return "", ""


def build_row_candidates(lines):

    row_candidates = []
    current_row = ""

    # OCR may add symbols around serial numbers: "[5", "12.", "2_|"
    serial_row_pattern = r"^\s*[\[\(\{\|_\-]*\s*\d+[\.)\]|_:\-]*\s*"

    for raw_line in lines:
        line = raw_line.strip()

        if not line or is_noise_line(line):
            continue

        if re.match(serial_row_pattern, line):
            if current_row:
                row_candidates.append(current_row)
            current_row = line
        else:
            # Join wrapped line fragments (common in PDFs/ocr tables).
            if current_row:
                current_row = f"{current_row} {line}"
            else:
                # Free-form lists may have one item per line without serial numbers.
                row_candidates.append(line)

    if current_row:
        row_candidates.append(current_row)

    return row_candidates


def find_canonical_vegetable_name(text):

    material = normalize_material_name(text)

    for alias in sorted(
        VEGETABLE_ALIASES.keys(),
        key=len,
        reverse=True,
    ):
        if alias in material:
            return VEGETABLE_ALIASES[alias]

    return ""


def is_candidate_line(line):

    if is_noise_line(line):
        return False

    has_alpha = bool(re.search(r"[A-Za-z]", line))
    has_qty = bool(re.search(r"\b(\d+(?:\.\d+)?)\s*(KG|KGS|NOS|EA)\b", line, flags=re.IGNORECASE))
    has_unit_then_num = bool(re.search(r"\b(KG|KGS|NOS|EA)\b\s*\d", line, flags=re.IGNORECASE))
    has_item_code = bool(re.search(r"\b\d{6,7}\b", line))

    return has_alpha and (has_qty or has_unit_then_num or has_item_code)


def build_extraction_report(results, unmatched_lines, candidate_count, total_lines):

    extracted_count = len(results)
    with_quantity = sum(1 for item in results if item.get("Quantity", "").strip())
    high_confidence = sum(1 for item in results if item.get("Confidence") == "High")

    return {
        "total_lines": total_lines,
        "candidate_lines": candidate_count,
        "extracted_rows": extracted_count,
        "with_quantity": with_quantity,
        "without_quantity": max(extracted_count - with_quantity, 0),
        "high_confidence": high_confidence,
        "unmatched_lines": unmatched_lines,
    }



def detect_vegetables(text, return_details=False):

    """
    Parse item rows from PO/table style text and capture quantities.
    """

    if not text:
        empty_report = build_extraction_report([], [], 0, 0)
        return ([], empty_report) if return_details else []

    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    row_candidates = build_row_candidates(lines)
    results = []
    unmatched_lines = []
    candidate_count = len(row_candidates)

    for idx, row in enumerate(row_candidates, start=1):

        material, quantity = extract_row_fields(row)
        material_for_match = material if material else row

        canonical_name = find_canonical_vegetable_name(material_for_match)

        if not canonical_name:
            unmatched_lines.append(
                {
                    "Line": idx,
                    "Text": row,
                }
            )
            continue

        if not quantity:
            quantity = extract_row_quantity(row)

        source_name = canonical_name.title()
        tamil_name = VEGETABLE_TAMIL_MAP.get(canonical_name, "")

        results.append(
            {
                "Source Name": source_name,
                "Tamil Name": tamil_name,
                "Quantity": quantity,
                "Status": "Needs Review" if not quantity else "Auto Extracted",
                "Confidence": "High" if quantity else "Medium",
            }
        )

    if results:
        report = build_extraction_report(
            results,
            unmatched_lines,
            candidate_count,
            len(lines),
        )
        return (results, report) if return_details else results

    # Fallback for very noisy text: detect name only.
    normalized_text = normalize_material_name(text)

    seen_fallback = set()

    for alias, canonical_name in VEGETABLE_ALIASES.items():
        if alias in normalized_text:
            if canonical_name in seen_fallback:
                continue

            seen_fallback.add(canonical_name)
            results.append(
                {
                    "Source Name": canonical_name.title(),
                    "Tamil Name": VEGETABLE_TAMIL_MAP.get(canonical_name, ""),
                    "Quantity": "",
                    "Status": "Needs Review",
                    "Confidence": "Low",
                }
            )

    report = build_extraction_report(
        results,
        unmatched_lines,
        candidate_count,
        len(lines),
    )

    return (results, report) if return_details else results



# ============================================================
# CONSOLIDATION
# ============================================================


def consolidate(df):

    if df.empty:
        return df


    working_df = df.copy()

    working_df["Quantity_Value"] = pd.to_numeric(
        working_df["Quantity"].astype(str).str.extract(r"(\d+\.?\d*)")[0],
        errors="coerce",
    ).fillna(0.0)

    working_df["Unit"] = (
        working_df["Quantity"]
        .astype(str)
        .str.extract(r"\b(KG|KGS|EA|NOS)\b", flags=re.IGNORECASE)[0]
        .str.upper()
        .replace({"KGS": "KG", "NOS": "EA"})
        .fillna("KG")
    )

    result = (
        working_df.groupby(["Tamil Name", "Unit"])
        ["Quantity_Value"]
        .sum()
        .reset_index()
    )

    result.rename(
        columns={
            "Quantity_Value": "Total Quantity"
        },
        inplace=True
    )

    return result



# ============================================================
# EXPORT FUNCTIONS
# ============================================================


def export_excel(
    df,
    logo_path="",
    header_text="PKS Fresh",
    above_list_text="காய்கறி பட்டியல்",
    footer_text="",
):

    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Font
    from openpyxl.styles import Alignment

    output = io.BytesIO()
    date_str = date.today().strftime("%d-%m-%Y")
    tamil_font_name = "Nirmala UI"
    export_df = df.copy()

    # Keep an extra blank column in downloaded list.
    if " " not in export_df.columns:
        export_df[" "] = ""

    date_line_text = f"தேதி: {date_str}"
    if str(above_list_text or "").strip():
        date_line_text = f"{date_line_text}    |    {str(above_list_text)}"

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Vegetables",
            startrow=6,
        )

        ws = writer.sheets["Vegetables"]

        ws["A1"] = str(header_text or "")
        ws["A3"] = date_line_text

        ws["A1"].font = Font(size=18, bold=True)
        ws["A3"].font = Font(name=tamil_font_name, size=13)

        ws["A1"].alignment = Alignment(horizontal="left")
        ws["A3"].alignment = Alignment(horizontal="left")

        ws.column_dimensions["A"].width = 36
        ws.column_dimensions["B"].width = 10
        ws.column_dimensions["C"].width = 12
        ws.column_dimensions["D"].width = 14
        ws.row_dimensions[3].height = 24

        header_row = 7
        ws[f"A{header_row}"].font = Font(size=12, bold=True)
        ws[f"B{header_row}"].font = Font(size=12, bold=True)
        ws[f"C{header_row}"].font = Font(size=12, bold=True)
        ws[f"D{header_row}"].font = Font(size=12, bold=True)

        for row_idx in range(header_row + 1, header_row + 1 + len(export_df)):
            ws[f"A{row_idx}"].font = Font(name=tamil_font_name, size=14)
            ws[f"A{row_idx}"].alignment = Alignment(wrap_text=True)
            ws.row_dimensions[row_idx].height = 24

        if str(footer_text or "").strip():
            footer_row = header_row + 2 + len(export_df)
            ws[f"A{footer_row}"] = str(footer_text)
            ws[f"A{footer_row}"].font = Font(name=tamil_font_name, size=12, bold=True)
            ws[f"A{footer_row}"].alignment = Alignment(horizontal="left", wrap_text=True)

        if logo_path and Path(logo_path).exists():
            logo_img = XLImage(str(logo_path))
            logo_img.height = 85
            logo_img.width = 150
            ws.add_image(logo_img, "D1")


    return output.getvalue()


def bytes_to_data_uri(image_bytes, file_name="logo.png"):

    mime_type = mimetypes.guess_type(file_name)[0] or "image/png"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def get_default_logo_data_uri():

    candidates = [
        Path("assets/PKS_Logo.jpeg"),
        Path("assets/logo.png"),
        Path("assets/logo.jpg"),
        Path("assets/logo.jpeg"),
    ]

    for logo_path in candidates:
        if logo_path.exists():
            image_bytes = logo_path.read_bytes()
            return bytes_to_data_uri(image_bytes, logo_path.name)

    return ""


def get_default_logo_path():

    candidates = [
        Path("assets/PKS_Logo.jpeg"),
        Path("assets/logo.png"),
        Path("assets/logo.jpg"),
        Path("assets/logo.jpeg"),
    ]

    for logo_path in candidates:
        if logo_path.exists():
            return str(logo_path)

    return ""


def push_validated_items_to_google_sheet(df):

    if df is None or len(df) == 0:
        return False, "No validated rows to push."

    if gspread is None or Credentials is None:
        return False, "Google Sheets libraries are not installed. Add gspread and google-auth dependencies."

    sheet_cfg = st.secrets.get("google_sheet", {})
    spreadsheet_id = sheet_cfg.get("spreadsheet_id", st.secrets.get("GOOGLE_SHEET_ID", ""))
    worksheet_name = sheet_cfg.get("worksheet", st.secrets.get("GOOGLE_SHEET_WORKSHEET", "Sheet1"))
    creds_info = st.secrets.get("gcp_service_account", sheet_cfg.get("service_account", None))

    if not spreadsheet_id:
        return False, "Google Sheet ID is missing. Configure it in Streamlit secrets."

    if not creds_info:
        return False, "Service account credentials are missing. Configure gcp_service_account in Streamlit secrets."

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds = Credentials.from_service_account_info(dict(creds_info), scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
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


def get_csv_path_for_date(date_str):

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"validated_{date_str}.csv"


def get_daily_csv_path():

    return get_csv_path_for_date(date.today().isoformat())


def list_saved_dates():

    out_dir = Path("outputs")
    if not out_dir.exists():
        return []

    dates = []
    for path in out_dir.glob("validated_*.csv"):
        match = re.match(r"validated_(\d{4}-\d{2}-\d{2})\.csv$", path.name)
        if match:
            dates.append(match.group(1))

    return sorted(set(dates), reverse=True)


def load_saved_rows_for_date(date_str):

    csv_path = get_csv_path_for_date(date_str)
    if not csv_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(csv_path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()


def load_saved_rows_for_today():

    csv_path = get_daily_csv_path()
    if not csv_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(csv_path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()


def persist_uploaded_image(uploaded_image_file):

    if uploaded_image_file is None:
        return ""

    date_str = date.today().isoformat()
    upload_dir = Path("outputs") / "uploads" / date_str
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(str(uploaded_image_file.name)).name
    out_path = upload_dir / safe_name
    out_path.write_bytes(uploaded_image_file.getvalue())

    return str(out_path)


def save_validated_items_to_csv(
    df,
    source_file,
    replace_existing=True,
    target_date=None,
    upload_type="",
    uploaded_image_path="",
):

    if df is None or len(df) == 0:
        return False, "No validated rows to save."

    date_str = target_date or date.today().isoformat()
    out_path = get_csv_path_for_date(date_str)
    source_file = str(source_file or "Unknown_File")

    write_df = df.copy()
    write_df["Date"] = date_str
    write_df["Source File"] = source_file
    write_df["Upload Type"] = str(upload_type or "")
    write_df["Uploaded Image Path"] = str(uploaded_image_path or "")
    write_df["Saved At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_df = write_df.fillna("")

    if out_path.exists():
        existing_df = pd.read_csv(out_path, dtype=str).fillna("")
    else:
        existing_df = pd.DataFrame()

    replaced_count = 0
    if replace_existing and not existing_df.empty and "Source File" in existing_df.columns:
        replaced_count = int((existing_df["Source File"] == source_file).sum())
        existing_df = existing_df[existing_df["Source File"] != source_file]

    combined_df = pd.concat([existing_df, write_df], ignore_index=True)

    combined_df.to_csv(out_path, index=False, encoding="utf-8-sig")

    if replaced_count > 0:
        return True, f"Updated {len(write_df)} row(s) for {source_file} in {out_path}."

    return True, f"Saved {len(write_df)} row(s) for {source_file} to {out_path}."


def remove_saved_file_from_csv(target_date, source_file):

    out_path = get_csv_path_for_date(target_date)
    if not out_path.exists():
        return False, f"No CSV found for {target_date}."

    existing_df = pd.read_csv(out_path, dtype=str).fillna("")
    if existing_df.empty or "Source File" not in existing_df.columns:
        return False, "No removable records found."

    rows_for_file = existing_df[existing_df["Source File"] == source_file].copy()
    if rows_for_file.empty:
        return False, f"No rows found for {source_file}."

    filtered_df = existing_df[existing_df["Source File"] != source_file].copy()

    # Clean up persisted uploaded images referenced by removed rows.
    if "Uploaded Image Path" in rows_for_file.columns:
        image_paths = rows_for_file["Uploaded Image Path"].astype(str).str.strip().unique().tolist()
        for img in image_paths:
            if img and Path(img).exists():
                try:
                    Path(img).unlink()
                except OSError:
                    pass

    if filtered_df.empty:
        out_path.unlink(missing_ok=True)
        return True, f"Removed {len(rows_for_file)} row(s) for {source_file}."

    filtered_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return True, f"Removed {len(rows_for_file)} row(s) for {source_file}."



def export_pdf(
    df,
    logo_data_uri="",
    header_text="PKS Fresh",
    above_list_text="காய்கறி பட்டியல்",
    footer_text="",
):
    from weasyprint import HTML

    date_str = date.today().strftime("%d-%m-%Y")

    rows_html = ""
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        bg = "#f2f2f2" if i % 2 == 0 else "#ffffff"
        tamil = str(row.get("Tamil Name", ""))
        total_qty = row.get("Total Quantity", "")
        unit = str(row.get("Unit", "KG"))
        try:
            qty_val = float(total_qty)
            qty_str = f"{qty_val:.0f}" if qty_val == int(qty_val) else f"{qty_val:.2f}"
        except (ValueError, TypeError):
            qty_str = str(total_qty)
        rows_html += (
            f'<tr style="background:{bg}">'
            f"<td>{i}</td>"
            f"<td>{tamil}</td>"
            f'<td class="num">{qty_str}</td>'
            f'<td class="num">{unit}</td>'
            "<td></td>"
            "</tr>"
        )

    logo_html = ""
    if logo_data_uri:
        logo_html = (
            '<div class="brand-logo-wrap">'
            f'<img class="brand-logo" src="{logo_data_uri}" alt="Company Logo" />'
            "</div>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="ta">
<head>
<meta charset="UTF-8">
<style>
  @font-face {{
    font-family: 'TamilFont';
        src: local('Noto Sans Tamil'), local('Lohit Tamil'), local('Tamil Sangam MN'), local('Tamil MN');
  }}
  body {{
        font-family: 'Noto Sans Tamil', 'Lohit Tamil', 'Tamil Sangam MN', 'Tamil MN', serif;
    margin: 40px;
    color: #111;
  }}
  h1 {{
    text-align: center;
    font-size: 26px;
    margin-bottom: 4px;
    letter-spacing: 1px;
  }}
    .brand-logo-wrap {{
        text-align: center;
        margin-bottom: 10px;
    }}
    .brand-logo {{
        max-height: 90px;
        max-width: 180px;
        object-fit: contain;
    }}
  .subtitle {{
    text-align: center;
    font-size: 13px;
    color: #555;
    margin-bottom: 4px;
  }}
  .date-line {{
        text-align: left;
    font-size: 11px;
    color: #444;
    margin-bottom: 14px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  thead tr {{
    background: #2c3e50;
    color: #fff;
  }}
  th {{
    padding: 9px 14px;
    font-size: 13px;
    text-align: left;
  }}
  th.num {{ text-align: right; }}
  td {{
    padding: 8px 14px;
    font-size: 13px;
    border-bottom: 1px solid #ddd;
  }}
  td.num {{ text-align: right; }}
  tfoot td {{
    font-weight: bold;
    border-top: 2px solid #2c3e50;
    padding: 8px 14px;
    font-size: 12px;
  }}
    .footer-note {{
        margin-top: 14px;
        font-size: 12px;
        color: #222;
        font-weight: 600;
    }}
</style>
</head>
<body>
    {logo_html}
    <h1>{str(header_text or '')}</h1>
    <div class="subtitle">காய்கறி பட்டியல்</div>
    <div class="date-line">{str(above_list_text or '')}  &nbsp;&nbsp; &nbsp;&nbsp;  தேதி: {date_str}</div>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>காய்கறி பெயர்</th>
        <th class="num">அளவு</th>
        <th class="num">அலகு</th>
                <th></th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
    <tfoot>
      <tr>
                <td colspan="3">மொத்தம் {len(df)} பொருட்கள்</td>
                <td class="num" colspan="2"></td>
      </tr>
    </tfoot>
  </table>
    <div class="footer-note">{str(footer_text or '')}</div>
</body>
</html>"""

    output = io.BytesIO()
    HTML(string=html_content).write_pdf(output)
    return output.getvalue()


def get_download_text_customization(scope_key):

    with st.expander("📝 Download Text Customization", expanded=False):
        header_text = st.text_input(
            "Header",
            value=st.session_state.get("download_header_text", "PKS Fresh"),
            key=f"download_header_text_{scope_key}",
        )
        above_list_text = st.text_input(
            "Just Above The List",
            value=st.session_state.get("download_above_list_text", "காய்கறி பட்டியல்"),
            key=f"download_above_list_text_{scope_key}",
        )
        footer_text = st.text_area(
            "Footer",
            value=st.session_state.get("download_footer_text", ""),
            key=f"download_footer_text_{scope_key}",
        )

    st.session_state["download_header_text"] = header_text
    st.session_state["download_above_list_text"] = above_list_text
    st.session_state["download_footer_text"] = footer_text

    return header_text, above_list_text, footer_text



# ============================================================
# STREAMLIT UI
# ============================================================


st.title("🥕 VegSense AI")
st.subheader(
    "Multilingual Vegetable Document Extractor"
)

st.session_state["print_logo_data_uri"] = get_default_logo_data_uri()

tab_primary, tab_saved, tab_consolidated = st.tabs(
    [
        "Upload Order",
        "Saved Orders",
        "Consolidated Orders",
    ]
)

with tab_primary:
    today_saved_df = load_saved_rows_for_today()
    st.info(
        "Status: "
        f"Active file = {st.session_state.get('active_source_file', 'None') or 'None'} | "
        f"Extracted rows = {len(st.session_state.get('items', []))} | "
        f"Confirmed rows = {len(st.session_state.get('validated_items', []))} | "
        f"Saved today = {len(today_saved_df)}"
    )

    uploaded_file = st.file_uploader(
        "Upload PDF / Image / Excel",
        type=[
            "pdf",
            "png",
            "jpg",
            "jpeg",
            "xlsx"
        ]
    )

    if uploaded_file:
        filename = uploaded_file.name.lower()
        st.session_state["active_source_file"] = uploaded_file.name

        st.success(
            f"Uploaded: {uploaded_file.name}"
        )

        if filename.endswith((".png", ".jpg", ".jpeg")):
            st.session_state["active_upload_type"] = "image"
            st.session_state["active_uploaded_image_path"] = persist_uploaded_image(uploaded_file)

            image = read_image(uploaded_file)

            st.image(
                image,
                caption="Uploaded Document",
                use_container_width=True
            )

            image_text, image_error = extract_image_text(image)

            if image_error:
                st.warning(image_error)
            else:
                st.session_state.raw_text = image_text

                st.subheader(
                    "Extracted Image Text"
                )

                st.text_area(
                    "Text",
                    image_text,
                    height=250
                )

        elif filename.endswith(".pdf"):
            st.session_state["active_upload_type"] = "pdf"
            st.session_state["active_uploaded_image_path"] = ""

            text = read_pdf(uploaded_file)
            st.session_state.raw_text = text

            st.subheader("Extracted PDF Text")
            st.text_area("Text", text, height=250)

        elif filename.endswith(".xlsx"):
            st.session_state["active_upload_type"] = "excel"
            st.session_state["active_uploaded_image_path"] = ""

            df = read_excel(uploaded_file)

            st.subheader("Excel Preview")
            st.dataframe(df, use_container_width=True)

            st.session_state.raw_text = df.to_string()

    if st.button("🔍 Extract Vegetables"):
        items, extraction_report = detect_vegetables(
            st.session_state.raw_text,
            return_details=True,
        )

        st.session_state["items"] = items
        st.session_state["extraction_report"] = extraction_report

        if items:
            st.success(f"{len(items)} vegetables detected")
        else:
            st.warning("No vegetables detected")

    if st.session_state["items"]:
        st.subheader("✏️ Validate Extraction")

        try:
            items_list = list(st.session_state["items"]) if st.session_state["items"] else []
            df = pd.DataFrame(items_list)
        except (ValueError, TypeError) as e:
            st.error(f"Error creating table: {e}")
            df = pd.DataFrame(columns=["Source Name", "Tamil Name", "Quantity", "Status"])

        with st.expander("➕ Add Missing Vegetable", expanded=False):
            st.caption("Pick a known English name (or use custom) to auto-map Tamil and append a new row.")

            alias_options = sorted({alias.title() for alias in VEGETABLE_ALIASES.keys()})
            alias_options.append("Custom...")

            selected_alias = st.selectbox(
                "English Name",
                options=alias_options,
                index=0,
                key="manual_english_name_select",
                help="Start typing to quickly search and pick a known alias.",
            )

            add_col_1, add_col_2 = st.columns([2, 1])

            with add_col_1:
                manual_name = ""
                if selected_alias == "Custom...":
                    manual_name = st.text_input(
                        "Custom English Name",
                        placeholder="e.g. Ladies Finger, Onion Big, Brinjal",
                        key="manual_english_name_custom",
                    )

            with add_col_2:
                manual_qty = st.text_input(
                    "Quantity",
                    placeholder="e.g. 5 KG",
                    key="manual_quantity",
                )

            if st.button("Add Row", key="add_manual_row"):
                name_value = manual_name.strip() if selected_alias == "Custom..." else selected_alias.strip()

                if not name_value:
                    st.warning("Enter an English vegetable name before adding.")
                else:
                    canonical_name = find_canonical_vegetable_name(name_value)

                    if not canonical_name:
                        normalized_name = normalize_text(name_value)
                        if normalized_name in VEGETABLE_TAMIL_MAP:
                            canonical_name = normalized_name

                    if not canonical_name:
                        st.warning(
                            "Vegetable name not recognized. Try a known alias such as 'Ladies Finger' or 'Coriander Leaves'."
                        )
                    else:
                        st.session_state["items"].append(
                            {
                                "Source Name": canonical_name.title(),
                                "Tamil Name": VEGETABLE_TAMIL_MAP.get(canonical_name, ""),
                                "Quantity": manual_qty.strip(),
                                "Status": "Manually Added",
                                "Confidence": "Manual",
                            }
                        )
                        st.success(f"Added: {canonical_name.title()}")
                        st.rerun()

        left_col, right_col = st.columns([1, 2])

        with left_col:
            st.markdown("### Extraction Quality")

            report = st.session_state.get("extraction_report", {})

            st.metric("Candidate Rows", report.get("candidate_lines", 0))
            st.metric("Extracted Rows", report.get("extracted_rows", 0))
            st.metric("Rows With Quantity", report.get("with_quantity", 0))
            st.metric("High Confidence", report.get("high_confidence", 0))

            unmatched_lines = report.get("unmatched_lines", [])

            if unmatched_lines:
                with st.expander("Unmatched Candidate Lines", expanded=False):
                    st.dataframe(
                        pd.DataFrame(unmatched_lines),
                        use_container_width=True,
                    )
            else:
                st.caption("No unmatched candidate lines detected.")

        with right_col:
            edited_df = st.data_editor(
                df,
                use_container_width=True
            )

        st.checkbox(
            "Also push confirmed rows to Google Sheet",
            key="push_gsheet_on_confirm",
            help="CSV save is always done. Enable this only when Sheet secrets are configured.",
        )

        if st.button("✅ Confirm"):
            st.session_state["validated_items"] = edited_df
            st.success("Validated successfully")

            source_file = st.session_state.get("active_source_file", "Unknown_File")
            csv_ok, csv_msg = save_validated_items_to_csv(
                edited_df,
                source_file=source_file,
                replace_existing=True,
                upload_type=st.session_state.get("active_upload_type", ""),
                uploaded_image_path=st.session_state.get("active_uploaded_image_path", ""),
            )
            if csv_ok:
                st.info(csv_msg)
            else:
                st.warning(csv_msg)

            if st.session_state.get("push_gsheet_on_confirm", False):
                push_ok, push_msg = push_validated_items_to_google_sheet(edited_df)
                if push_ok:
                    st.info(push_msg)
                else:
                    st.warning(push_msg)

        if len(st.session_state["validated_items"]):
            st.subheader("✅ Confirmed Output")
            confirmed_df = consolidate(st.session_state["validated_items"])
            st.dataframe(confirmed_df, use_container_width=True)

            dl_header, dl_above, dl_footer = get_download_text_customization("confirmed")

            confirmed_excel = export_excel(
                confirmed_df,
                logo_path=get_default_logo_path(),
                header_text=dl_header,
                above_list_text=dl_above,
                footer_text=dl_footer,
            )
            confirmed_pdf = export_pdf(
                confirmed_df,
                logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                header_text=dl_header,
                above_list_text=dl_above,
                footer_text=dl_footer,
            )

            st.download_button(
                "⬇️ Download Confirmed Excel",
                confirmed_excel,
                file_name="confirmed_vegetables.xlsx"
            )
            st.download_button(
                "⬇️ Download Confirmed PDF",
                confirmed_pdf,
                file_name="confirmed_vegetables.pdf"
            )

with tab_saved:
    st.subheader("🗂️ Saved Orders")

    saved_dates_for_tab = list_saved_dates()
    if not saved_dates_for_tab:
        st.info("Status: No saved dates yet.")
    else:
        st.info(f"Status: Available saved dates = {len(saved_dates_for_tab)}")

    with st.expander("Saved Records and Revalidation", expanded=False):
        available_dates = saved_dates_for_tab

        if not available_dates:
            st.caption("No saved rows yet. Validate and confirm a file to create output CSV.")
        else:
            selected_saved_date = st.selectbox(
                "Select date",
                options=available_dates,
                key="selected_saved_date_tab",
            )

            saved_by_date_df = load_saved_rows_for_date(selected_saved_date)
            file_count = 0
            if not saved_by_date_df.empty and "Source File" in saved_by_date_df.columns:
                file_count = saved_by_date_df["Source File"].nunique()
            st.info(
                f"Status: Date = {selected_saved_date} | Rows = {len(saved_by_date_df)} | Files = {file_count}"
            )

            if saved_by_date_df.empty:
                st.caption("No rows found for selected date.")
            else:
                st.caption(f"Loaded {len(saved_by_date_df)} rows from {get_csv_path_for_date(selected_saved_date)}")

                if "Source File" in saved_by_date_df.columns:
                    source_files = sorted(saved_by_date_df["Source File"].astype(str).unique().tolist())
                else:
                    source_files = []

                if source_files:
                    selected_saved_file = st.selectbox(
                        "Choose file",
                        options=source_files,
                        key="individual_saved_file_tab",
                    )

                    selected_df = saved_by_date_df[saved_by_date_df["Source File"] == selected_saved_file].copy()

                    img_path = ""
                    if "Uploaded Image Path" in selected_df.columns and not selected_df.empty:
                        img_path = str(selected_df["Uploaded Image Path"].iloc[0]).strip()

                    if selected_saved_date == date.today().isoformat() and img_path and Path(img_path).exists():
                        st.image(img_path, caption=f"Uploaded image: {selected_saved_file}", use_container_width=True)

                    display_cols = [
                        col
                        for col in ["Source Name", "Tamil Name", "Quantity", "Status", "Confidence"]
                        if col in selected_df.columns
                    ]

                    editable_df = st.data_editor(
                        selected_df[display_cols],
                        use_container_width=True,
                        key="saved_revalidate_editor_tab",
                    )

                    action_col_1, action_col_2 = st.columns(2)

                    with action_col_1:
                        overwrite_clicked = st.button(
                            "💾 Overwrite Saved File",
                            key="update_saved_file_btn_tab",
                        )

                    with action_col_2:
                        remove_clicked = st.button(
                            "🗑️ Remove Selected Upload",
                            key="remove_saved_file_btn_tab",
                        )

                    if overwrite_clicked:
                        upload_type = ""
                        if "Upload Type" in selected_df.columns and not selected_df.empty:
                            upload_type = str(selected_df["Upload Type"].iloc[0]).strip()

                        upd_ok, upd_msg = save_validated_items_to_csv(
                            editable_df,
                            source_file=selected_saved_file,
                            replace_existing=True,
                            target_date=selected_saved_date,
                            upload_type=upload_type,
                            uploaded_image_path=img_path,
                        )
                        if upd_ok:
                            st.success(upd_msg)
                            st.rerun()
                        else:
                            st.warning(upd_msg)

                    if remove_clicked:
                        rem_ok, rem_msg = remove_saved_file_from_csv(
                            selected_saved_date,
                            selected_saved_file,
                        )
                        if rem_ok:
                            st.success(rem_msg)
                            st.rerun()
                        else:
                            st.warning(rem_msg)

                    individual_df = consolidate(editable_df)
                    st.markdown("### Download Individual Order")
                    st.dataframe(individual_df, use_container_width=True)

                    dl_header, dl_above, dl_footer = get_download_text_customization("individual")

                    individual_excel = export_excel(
                        individual_df,
                        logo_path=get_default_logo_path(),
                        header_text=dl_header,
                        above_list_text=dl_above,
                        footer_text=dl_footer,
                    )
                    individual_pdf = export_pdf(
                        individual_df,
                        logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                        header_text=dl_header,
                        above_list_text=dl_above,
                        footer_text=dl_footer,
                    )

                    st.download_button(
                        "⬇️ Download Individual Excel",
                        individual_excel,
                        file_name=f"individual_{selected_saved_file}_{selected_saved_date}.xlsx"
                    )
                    st.download_button(
                        "⬇️ Download Individual PDF",
                        individual_pdf,
                        file_name=f"individual_{selected_saved_file}_{selected_saved_date}.pdf"
                    )

with tab_consolidated:
    st.subheader("📦 Consolidated Orders")

    consolidated_dates = list_saved_dates()
    if not consolidated_dates:
        st.info("Status: No saved dates available for consolidation.")
    else:
        st.info(f"Status: Available dates for consolidation = {len(consolidated_dates)}")

    with st.expander("Consolidated Records", expanded=False):
        available_dates = consolidated_dates

        if not available_dates:
            st.caption("No saved rows available yet.")
        else:
            selected_records_date = st.selectbox(
                "Select date",
                options=available_dates,
                key="selected_records_date_tab",
            )

            saved_by_date_df = load_saved_rows_for_date(selected_records_date)
            st.info(
                f"Status: Date = {selected_records_date} | Source rows = {len(saved_by_date_df)}"
            )

            if saved_by_date_df.empty:
                st.caption("No rows found for selected date.")
            else:
                final_df = consolidate(saved_by_date_df)

                st.dataframe(final_df, use_container_width=True)

                dl_header, dl_above, dl_footer = get_download_text_customization("consolidated")

                excel_file = export_excel(
                    final_df,
                    logo_path=get_default_logo_path(),
                    header_text=dl_header,
                    above_list_text=dl_above,
                    footer_text=dl_footer,
                )

                pdf_file = export_pdf(
                    final_df,
                    logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                    header_text=dl_header,
                    above_list_text=dl_above,
                    footer_text=dl_footer,
                )

                st.download_button(
                    "⬇️ Download Consolidated Excel",
                    excel_file,
                    file_name=f"vegetables_{selected_records_date}.xlsx"
                )

                st.download_button(
                    "⬇️ Download Consolidated PDF",
                    pdf_file,
                    file_name=f"vegetables_{selected_records_date}.pdf"
                )



st.divider()

st.caption(
    "Version 0.2 | OCR + quality review enabled"
)