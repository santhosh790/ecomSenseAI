import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import io
import shutil
from PIL import Image, ImageOps, ImageFilter
from datetime import date

try:
    import pytesseract
except ImportError:
    pytesseract = None

if pytesseract is not None:
    # Explicitly set binary path when available (helps on hosted runtimes).
    tesseract_binary = shutil.which("tesseract")
    if tesseract_binary:
        pytesseract.pytesseract.tesseract_cmd = tesseract_binary


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="VegSense AI",
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
    "CAPSICUM GREEN": "CAPSICUM",
    "CAPSICUM": "CAPSICUM",
    "CARROT": "CARROT",
    "CAULIFLOWER": "CAULIFLOWER",
    "CHOW CHOW": "CHOW CHOW",
    "COCONUT RAW NOS": "COCONUT",
    "COCONUT FRESH": "COCONUT",
    "COCONUT": "COCONUT",
    "CORIANDER FRESH": "CORIANDER",
    "CORIANDER LEAVES": "CORIANDER",
    "CORIANDER": "CORIANDER",
    "CUCUMBER": "CUCUMBER",
    "CURRY LEAVES": "CURRY LEAVES",
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
    value = re.sub(r"\b\d+X\d+(?:KG|KGS|NOS|EA)\b", " ", value)
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

    # PO style: "... 1 Kgs 90.00 90.00"
    qty_unit_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(KG|KGS|G|GM|GRAMS?|NOS|EA)\b",
        text,
        flags=re.IGNORECASE,
    )

    if qty_unit_match:
        qty = qty_unit_match.group(1)
        unit = qty_unit_match.group(2).upper()
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return f"{qty} {unit}"

    # Table style: "... KG 45 25.07.2026"
    unit_qty_match = re.search(
        r"\b(KG|KGS|NOS|EA)\b\s*(\d+(?:\.\d+)?)\b",
        text,
        flags=re.IGNORECASE,
    )

    if unit_qty_match:
        unit = unit_qty_match.group(1).upper()
        qty = unit_qty_match.group(2)
        if unit in ["KGS", "KG"]:
            unit = "KG"
        return f"{qty} {unit}"

    return ""


def extract_row_fields(text):

    compact = re.sub(r"\s+", " ", str(text)).strip()

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
        r"^\s*\d+\s+(?:\d+\s+)?(.+?)\s+(KG|KGS|NOS|EA)\s+(\d+(?:\.\d+)?)\b",
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

    return "", ""


def build_row_candidates(lines):

    row_candidates = []
    current_row = ""

    serial_row_pattern = r"^\s*\d+\s+"

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


def export_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Vegetables"
        )


    return output.getvalue()



def export_pdf(df):
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
            "</tr>"
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
  .subtitle {{
    text-align: center;
    font-size: 13px;
    color: #555;
    margin-bottom: 4px;
  }}
  .date-line {{
    text-align: right;
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
</style>
</head>
<body>
  <h1>PKS Foods</h1>
  <div class="subtitle">காய்கறி ஆர்டர் பட்டியல்</div>
  <div class="date-line">தேதி: {date_str}</div>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>காய்கறி பெயர்</th>
        <th class="num">அளவு</th>
        <th class="num">அலகு</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
    <tfoot>
      <tr>
        <td colspan="2">மொத்தம் {len(df)} பொருட்கள்</td>
        <td class="num" colspan="2"></td>
      </tr>
    </tfoot>
  </table>
</body>
</html>"""

    output = io.BytesIO()
    HTML(string=html_content).write_pdf(output)
    return output.getvalue()



# ============================================================
# STREAMLIT UI
# ============================================================


st.title("🥕 VegSense AI")
st.subheader(
    "Multilingual Vegetable Document Extractor"
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


    st.success(
        f"Uploaded: {uploaded_file.name}"
    )


    # -------------------------------
    # IMAGE
    # -------------------------------

    if filename.endswith(
        (".png",".jpg",".jpeg")
    ):

        image = read_image(
            uploaded_file
        )

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



    # -------------------------------
    # PDF
    # -------------------------------

    elif filename.endswith(".pdf"):


        text = read_pdf(
            uploaded_file
        )


        st.session_state.raw_text = text


        st.subheader(
            "Extracted PDF Text"
        )


        st.text_area(
            "Text",
            text,
            height=250
        )


    # -------------------------------
    # EXCEL
    # -------------------------------

    elif filename.endswith(".xlsx"):


        df = read_excel(
            uploaded_file
        )


        st.subheader(
            "Excel Preview"
        )


        st.dataframe(
            df,
            use_container_width=True
        )


        st.session_state.raw_text = (
            df.to_string()
        )



# ============================================================
# EXTRACTION BUTTON
# ============================================================


if st.button(
    "🔍 Extract Vegetables"
):


    items, extraction_report = detect_vegetables(
        st.session_state.raw_text,
        return_details=True,
    )


    st.session_state["items"] = items
    st.session_state["extraction_report"] = extraction_report


    if items:

        st.success(
            f"{len(items)} vegetables detected"
        )

    else:

        st.warning(
            "No vegetables detected"
        )



# ============================================================
# VALIDATION TABLE
# ============================================================


if st.session_state["items"]:


    st.subheader(
        "✏️ Validate Extraction"
    )

    try:
        # Ensure items is a list and create DataFrame
        items_list = list(st.session_state["items"]) if st.session_state["items"] else []
        df = pd.DataFrame(items_list)
    except (ValueError, TypeError) as e:
        st.error(f"Error creating table: {e}")
        df = pd.DataFrame(columns=["Source Name", "Tamil Name", "Quantity", "Status"])


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


    if st.button(
        "✅ Confirm"
    ):

        st.session_state["validated_items"] = (
            edited_df
        )

        st.success(
            "Validated successfully"
        )



# ============================================================
# CONSOLIDATION
# ============================================================


if len(
    st.session_state["validated_items"]
):


    st.subheader(
        "📦 Consolidated Output"
    )


    final_df = consolidate(
        st.session_state["validated_items"]
    )


    st.dataframe(
        final_df,
        use_container_width=True
    )



    excel_file = export_excel(
        final_df
    )


    pdf_file = export_pdf(
        final_df
    )


    st.download_button(
        "⬇️ Download Excel",
        excel_file,
        file_name="vegetables.xlsx"
    )


    st.download_button(
        "⬇️ Download PDF",
        pdf_file,
        file_name="vegetables.pdf"
    )



st.divider()

st.caption(
    "Version 0.2 | OCR + quality review enabled"
)