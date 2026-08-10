import streamlit as st
import pandas as pd
import json
import shutil
import logging
import traceback
from datetime import date
from pathlib import Path

# Configure logging for Streamlit Cloud
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import application services with error handling
try:
    from application.vegetable_detection_service import detect_vegetables as detect_vegetables_service
    from application.vegetable_detection_service import find_canonical_vegetable_name as find_canonical_vegetable_name_service
    from application.vegetable_catalog_service import load_vegetable_catalog
    from application.reporting_service import consolidate, consolidate_with_client_columns, export_excel, export_pdf, export_delivery_challan_excel, export_delivery_challan_pdf
    from application.extraction_service import normalize_text as normalize_text_service
    from infrastructure.assets_service import get_default_logo_data_uri, get_default_logo_path
    from infrastructure.document_readers import (
        read_excel,
        read_image,
        read_pdf,
    )
    from infrastructure.google_sheets_service import push_validated_items_to_google_sheet, push_consolidated_to_google_sheet
    from infrastructure.ocr_engine import extract_image_text as extract_image_text_service
    from infrastructure.ocr_engine import load_ocr_model
    from infrastructure.address_service import (
        load_addresses,
        add_bill_to_address,
        add_ship_to_address,
        get_bill_to_names,
        get_ship_to_names,
        get_bill_to_address,
        get_ship_to_address,
    )
    from infrastructure.persistence_service import (
        get_csv_path_for_date,
        list_saved_dates,
        load_saved_rows_for_date,
        load_saved_rows_for_today,
        persist_uploaded_image,
        remove_saved_file_from_csv,
        save_validated_items_to_csv,
    )
    logger.info("✓ All application modules loaded successfully")
except Exception as e:
    logger.error(f"Failed to import application modules: {e}\n{traceback.format_exc()}")
    st.error(f"**Critical Import Error:** {e}")
    st.code(traceback.format_exc())
    st.stop()

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
# CLIENT MANAGEMENT
# ============================================================

def load_clients():
    """Load client names from data/clients.json file.
    Returns dict mapping full name to short name.
    """
    clients_file = Path("data") / "clients.json"
    if not clients_file.exists():
        return {}
    
    try:
        with open(clients_file, 'r', encoding='utf-8') as f:
            clients_dict = json.load(f)
        return clients_dict
    except Exception as e:
        logger.error(f"Error loading clients: {e}")
        return {}

def get_client_full_names():
    """Get list of full client names for dropdown selection."""
    clients_dict = load_clients()
    return sorted(clients_dict.keys())

def get_client_short_name(full_name):
    """Get short name for a client given the full name."""
    clients_dict = load_clients()
    return clients_dict.get(full_name, full_name)  # Fallback to full name if not found

def save_client(new_client_full, new_client_short=None):
    """Add a new client to data/clients.json file.
    
    Args:
        new_client_full: Full client name
        new_client_short: Short name for reports (defaults to full name if not provided)
    """
    if not new_client_full or not new_client_full.strip():
        return False
    
    new_client_full = new_client_full.strip()
    new_client_short = (new_client_short or new_client_full).strip()
    
    # Load existing clients
    existing_clients = load_clients()
    
    # Check if client already exists (case-insensitive)
    if new_client_full.upper() in [c.upper() for c in existing_clients.keys()]:
        return False  # Already exists
    
    # Add new client
    existing_clients[new_client_full] = new_client_short
    
    # Save back to file
    clients_file = Path("data") / "clients.json"
    clients_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Write as JSON with sorted keys
        sorted_clients = dict(sorted(existing_clients.items()))
        with open(clients_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_clients, f, indent=4, ensure_ascii=False)
        logger.info(f"Added new client: {new_client_full} -> {new_client_short}")
        return True
    except Exception as e:
        logger.error(f"Error saving client: {e}")
        return False


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="eComSense AI",
    page_icon="🥕",
    layout="wide"
)


VEGETABLE_CATALOG = load_vegetable_catalog()


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


# ============================================================
# DEPENDENCY HEALTH CHECK
# ============================================================

def check_deployment_health():
    """Check and report on optional dependencies and system state."""
    issues = []
    warnings = []
    info = []
    
    # Check Tesseract OCR
    if pytesseract is None:
        warnings.append("⚠️ Tesseract OCR not available - Image OCR disabled")
    else:
        tesseract_binary = shutil.which("tesseract")
        if tesseract_binary:
            info.append(f"✓ Tesseract OCR available at {tesseract_binary}")
        else:
            warnings.append("⚠️ Tesseract binary not found in PATH")
    
    # Check Google Sheets integration
    if gspread is None or Credentials is None:
        warnings.append("⚠️ Google Sheets integration not available")
    else:
        info.append("✓ Google Sheets integration available")
    
    # Check PaddleOCR
    try:
        import paddleocr
        info.append("✓ PaddleOCR available")
    except ImportError:
        warnings.append("⚠️ PaddleOCR not available - Advanced OCR disabled")
    except Exception as e:
        warnings.append(f"⚠️ PaddleOCR error: {str(e)[:50]}")
    
    # Check WeasyPrint (for PDF export)
    # Note: WeasyPrint requires system libraries that may not be available on macOS
    # It works best on Linux (Streamlit Cloud uses Linux)
    try:
        import weasyprint
        info.append("✓ WeasyPrint available for PDF export")
    except ImportError:
        warnings.append("⚠️ WeasyPrint not available - PDF export disabled")
    except OSError as e:
        # Common on macOS - missing system libraries
        if "libgobject" in str(e) or "libcairo" in str(e):
            warnings.append("⚠️ WeasyPrint: Missing system libraries (normal on macOS, works on Linux/Cloud)")
        else:
            warnings.append(f"⚠️ WeasyPrint error: {str(e)[:50]}")
    except Exception as e:
        warnings.append(f"⚠️ WeasyPrint error: {str(e)[:50]}")
    
    # Check OpenPyXL (for Excel export)
    try:
        import openpyxl
        info.append("✓ OpenPyXL available for Excel export")
    except ImportError:
        issues.append("❌ OpenPyXL not available - Excel export disabled")
    except Exception as e:
        issues.append(f"❌ OpenPyXL error: {str(e)[:50]}")
    
    # Log everything
    for msg in info:
        logger.info(msg)
    for msg in warnings:
        logger.warning(msg)
    for msg in issues:
        logger.error(msg)
    
    # Display to user if there are issues or warnings
    if issues or warnings:
        with st.expander("⚙️ System Status", expanded=bool(issues)):
            if issues:
                st.error("**Critical Issues:**")
                for issue in issues:
                    st.write(issue)
            if warnings:
                st.warning("**Warnings:**")
                for warning in warnings:
                    st.write(warning)
            if info:
                st.info("**Available Features:**")
                for i in info:
                    st.write(i)
    
    return len(issues) == 0

# Run health check
try:
    deployment_ok = check_deployment_health()
    if not deployment_ok:
        st.warning("⚠️ Some features may be limited due to missing dependencies")
except Exception as e:
    logger.error(f"Health check failed: {e}\n{traceback.format_exc()}")
    st.error(f"Health check error: {e}")

if "active_client_name" not in st.session_state:
    st.session_state["active_client_name"] = ""

if "parser_selection" not in st.session_state:
    st.session_state["parser_selection"] = "Generic"

if "confidence_auto_extract_threshold" not in st.session_state:
    st.session_state["confidence_auto_extract_threshold"] = 90

if "confidence_match_threshold" not in st.session_state:
    st.session_state["confidence_match_threshold"] = 75

if "active_upload_signature" not in st.session_state:
    st.session_state["active_upload_signature"] = ""

if "pdf_source_text" not in st.session_state:
    st.session_state["pdf_source_text"] = ""

if "pdf_detected_tables" not in st.session_state:
    st.session_state["pdf_detected_tables"] = []

if "pdf_mapped_rows" not in st.session_state:
    st.session_state["pdf_mapped_rows"] = []


# ============================================================
# UI ORCHESTRATION WRAPPERS
# ============================================================

@st.cache_resource
def load_ocr():
    return load_ocr_model()


def extract_image_text(image):
    return extract_image_text_service(image, ocr_model=load_ocr())

def normalize_text(text):
    return normalize_text_service(text)

def find_canonical_vegetable_name(text):
    confidence_match_threshold = int(st.session_state.get("confidence_match_threshold", 75))
    return find_canonical_vegetable_name_service(
        text,
        confidence_threshold=confidence_match_threshold,
    )


def detect_vegetables(text, return_details=False, parser_selection=None):
    confidence_match_threshold = int(st.session_state.get("confidence_match_threshold", 75))
    confidence_auto_extract_threshold = int(st.session_state.get("confidence_auto_extract_threshold", 90))
    
    # Use parser_selection if provided, otherwise use from session state
    if parser_selection is None:
        parser_selection = st.session_state.get("parser_selection", "Generic")
    
    # Map parser selection to client_name parameter
    # Generic = None (auto-detect), VIT/FVIT = pass as client_name
    client_name = None if parser_selection == "Generic" else parser_selection

    return detect_vegetables_service(
        text,
        return_details=return_details,
        confidence_threshold=confidence_match_threshold,
        auto_extract_threshold=confidence_auto_extract_threshold,
        client_name=client_name,
    )


def inject_mobile_first_styles():
    """Inject responsive styles for mobile-first Streamlit usage."""
    st.markdown(
        """
        <style>
        .stApp {
            -webkit-text-size-adjust: 100%;
        }

        .main .block-container {
            padding-top: 0.8rem;
            padding-bottom: 1rem;
        }

        /* Larger tap targets for mobile */
        div.stButton > button,
        div.stDownloadButton > button {
            min-height: 44px;
            border-radius: 10px;
            font-weight: 600;
        }

        /* Improve readability in tables on smaller screens */
        .stDataFrame,
        .stTable {
            font-size: 0.95rem;
        }

        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }

            div.stButton > button,
            div.stDownloadButton > button {
                width: 100%;
            }

            h1 {
                font-size: 1.6rem !important;
            }

            h2, h3 {
                font-size: 1.2rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# STREAMLIT UI
# ============================================================


inject_mobile_first_styles()


st.title("🛒 ecomSense AI")
st.subheader(
    "Multilingual Grocery Document Extractor"
)

with st.expander("📱 Install On Mobile (PWA-Style)", expanded=False):
    st.markdown(
        """
        **Android (Chrome):** Open app URL -> Tap menu (⋮) -> **Add to Home screen**

        **iPhone (Safari):** Open app URL -> Tap Share -> **Add to Home Screen**

        **Note:** This mode reuses your current Streamlit backend with zero extra server cost.
        """
    )

st.session_state["print_logo_data_uri"] = get_default_logo_data_uri()

tab_primary, tab_saved, tab_consolidated, tab_challan = st.tabs(
    [
        "Upload Order",
        "Saved Orders",
        "Consolidated Orders",
        "Delivery Challan",
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

    # Date selector for the order
    from datetime import date, timedelta
    st.session_state["active_order_date"] = st.date_input(
        "Order Date",
        value=st.session_state.get("active_order_date", date.today()),
        help="Select the date for this order. You can upload orders for different dates on the same day.",
        key="order_date_selector",
    )
    
    # Client Name Selection with Add New option
    available_clients = get_client_full_names()
    client_options = available_clients + ["➕ Add New Client..."]
    
    # Get current client or empty string
    current_client = st.session_state.get("active_client_name", "")
    
    # Determine default index
    if current_client and current_client in available_clients:
        default_idx = available_clients.index(current_client)
    else:
        default_idx = len(available_clients)  # "Add New Client..." option
    
    selected_client = st.selectbox(
        "Client Name",
        options=client_options,
        index=0,
        help="Select existing client or add a new one. Full name shown in dropdown, short name used in reports.",
        key="client_name_selector",
    )
    
    # Handle "Add New Client" option
    if selected_client == "➕ Add New Client...":
        col1, col2 = st.columns([2, 2])
        with col1:
            new_client_full = st.text_input(
                "Full Client Name",
                value="",
                placeholder="e.g., 'RASSENSE PVT LTD'",
                key="new_client_full_input",
            )
        with col2:
            new_client_short = st.text_input(
                "Short Name (for reports)",
                value="",
                placeholder="e.g., 'RASSENSE'",
                key="new_client_short_input",
            )
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if st.button("💾 Save", key="save_new_client"):
                if new_client_full.strip():
                    short_name = new_client_short.strip() or new_client_full.strip()
                    if save_client(new_client_full.strip(), short_name):
                        st.session_state["active_client_name"] = new_client_full.strip()
                        st.success(f"✅ Added: {new_client_full.strip()} → {short_name}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Client already exists")
                else:
                    st.warning("⚠️ Please enter a client name")
        # Keep previous client while adding new
        if not new_client_full:
            st.session_state["active_client_name"] = current_client
    else:
        st.session_state["active_client_name"] = selected_client
    
    # Parser selection dropdown
    parser_options = ["Generic", "VIT", "FVIT", "MHS"]
    st.session_state["parser_selection"] = st.selectbox(
        "Parser Strategy",
        options=parser_options,
        index=parser_options.index(st.session_state.get("parser_selection", "Generic")),
        help="Select the parsing strategy for extraction. Generic works for most formats.",
    )
    
    # Show supported parsers information in an expander
    with st.expander("ℹ️ Parser Strategy Information"):
        st.markdown("""
        **Available Parsers:**
        
        - **Generic** (Default): Works with most purchase order formats
          - Handles various column layouts
          - Automatically corrects OCR errors (Ko/Ke/Kq/Rg → KG)
          - Recommended for most documents
        
        - **VIT**: Optimized for VIT Purchase Orders
          - 11-12 column format
          - Includes item codes (6-7 digits)
          - Pattern: Serial | ItemCode | Material | HSN-UOM-Qty
        
        - **FVIT**: Optimized for FVIT Purchase Orders
          - 8 column format
          - Pattern: Serial | Material | HSN | UOM | Qty
        
        - **MHS**: Optimized for MHS Multi-line Purchase Requisitions
          - Multi-line format (3 lines per item)
          - Pattern: Item Name → Item Code (7 digits) → Quantity with UOM
          - Example: BABY CORN PEELED → 1100006 → 1 Kgs
        
        **Tips:**
        - Start with **Generic** - it handles most documents well
        - Switch to VIT/FVIT/MHS if Generic doesn't extract properly
        - The system automatically handles common OCR errors
        """)

    if uploaded_file:
        filename = uploaded_file.name.lower()
        current_signature = f"{uploaded_file.name}:{getattr(uploaded_file, 'size', 0)}"
        is_new_upload = st.session_state.get("active_upload_signature") != current_signature

        if is_new_upload:
            st.session_state["active_upload_signature"] = current_signature

        st.session_state["active_source_file"] = uploaded_file.name

        st.success(
            f"Uploaded: {uploaded_file.name}"
        )

        if filename.endswith((".png", ".jpg", ".jpeg")):
            st.session_state["active_upload_type"] = "image"
            st.session_state["active_uploaded_image_path"] = persist_uploaded_image(
                uploaded_file,
                target_date=st.session_state.get("active_order_date", date.today()).isoformat()
            )

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
                st.success("OCR completed")

            if st.session_state.raw_text:
                st.subheader("Extracted Image Text")
                st.text_area(
                    "Text",
                    st.session_state.raw_text,
                    height=250
                )

        elif filename.endswith(".pdf"):
            st.session_state["active_upload_type"] = "pdf"
            st.session_state["active_uploaded_image_path"] = ""

            if is_new_upload:
                st.session_state["pdf_source_text"] = read_pdf(uploaded_file)
                st.session_state.raw_text = st.session_state["pdf_source_text"]

            st.subheader("Extracted PDF Text")
            st.text_area("Text", st.session_state.raw_text, height=250, key="pdf_text_display")

        elif filename.endswith(".xlsx"):
            st.session_state["active_upload_type"] = "excel"
            st.session_state["active_uploaded_image_path"] = ""

            df = read_excel(uploaded_file)

            st.subheader("Excel Preview")
            st.dataframe(df, use_container_width=True)

            st.session_state.raw_text = df.to_string()

    with st.expander("Confidence Controls", expanded=False):
        st.session_state["confidence_match_threshold"] = st.slider(
            "Minimum OCR name-match confidence (%)",
            min_value=50,
            max_value=95,
            value=int(st.session_state.get("confidence_match_threshold", 75)),
            help="Rows below this fuzzy-match score are not auto-mapped to a grocery item.",
        )
        st.session_state["confidence_auto_extract_threshold"] = st.slider(
            "Auto-extract status threshold (%)",
            min_value=60,
            max_value=99,
            value=int(st.session_state.get("confidence_auto_extract_threshold", 90)),
            help="Rows below this score are marked as Needs Review even when quantity is present.",
        )

    if st.button("🔍 Extract Groceries"):
        client_name = st.session_state.get("active_client_name", "")
        parser_selection = st.session_state.get("parser_selection", "Generic")
        
        # Always use raw text extraction with selected parser
        items, extraction_report = detect_vegetables(
            st.session_state.raw_text,
            return_details=True,
            parser_selection=parser_selection,
        )

        st.session_state["items"] = items
        st.session_state["extraction_report"] = extraction_report

        # Display parser strategy and extraction stats
        parser_strategy = extraction_report.get("parser_strategy", "unknown")
        vit_activated = extraction_report.get("vit_mode_activated", False)
        vit_reason = extraction_report.get("vit_activation_reason", "")
        
        # Show parser info
        parser_display = parser_selection if parser_selection != "Generic" else parser_strategy.upper()
        status_icon = "🎯" if parser_selection != "Generic" else "🔍"
        
        st.info(
            f"{status_icon} **Parser Used:** {parser_display} | "
            f"**Extracted:** {len(items)} items | "
            f"**Parser Selection:** {parser_selection}"
        )

        if items:
            st.success(f"{len(items)} items detected")
        else:
            st.warning("No items detected")

    if st.session_state["items"]:
        st.subheader("✏️ Validate Extraction")

        try:
            items_list = list(st.session_state["items"]) if st.session_state["items"] else []
            df = pd.DataFrame(items_list)
            # Add a "Delete" column for row-level removal
            if not df.empty and "Delete" not in df.columns:
                df.insert(0, "Delete", False)
        except (ValueError, TypeError) as e:
            st.error(f"Error creating table: {e}")
            df = pd.DataFrame(columns=["Delete", "Source Name", "Tamil Name", "Quantity", "Status"])

        with st.expander("➕ Add Missing Item", expanded=False):
            st.caption("Pick a known English name (or use custom) to auto-map Tamil and append a new row.")

            alias_options = sorted({alias.title() for alias in VEGETABLE_CATALOG.vegetable_aliases.keys()})
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
                        if normalized_name in VEGETABLE_CATALOG.vegetable_tamil_map:
                            canonical_name = normalized_name

                    if not canonical_name:
                        st.warning(
                            "Vegetable name not recognized. Try a known alias such as 'Ladies Finger' or 'Coriander Leaves'."
                        )
                    else:
                        st.session_state["items"].append(
                            {
                                "Source Name": canonical_name.title(),
                                "Tamil Name": VEGETABLE_CATALOG.vegetable_tamil_map.get(canonical_name, ""),
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

            parser_strategy = str(report.get("parser_strategy", "generic")).strip() or "generic"
            st.caption(f"Parser strategy: {parser_strategy}")

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
            st.caption("💡 Tip: Check the 'Delete' box to remove unwanted rows from final export")
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                column_config={
                    "Delete": st.column_config.CheckboxColumn(
                        "🗑️ Delete",
                        help="Check to remove this row from final export",
                        default=False,
                    )
                },
                hide_index=True,
            )
        
        # Show deletion summary
        if not edited_df.empty and "Delete" in edited_df.columns:
            rows_marked_for_deletion = edited_df["Delete"].sum()
            rows_to_keep = len(edited_df) - rows_marked_for_deletion
            
            if rows_marked_for_deletion > 0:
                st.warning(f"⚠️ {rows_marked_for_deletion} row(s) marked for deletion | {rows_to_keep} row(s) will be saved")
            else:
                st.info(f"📊 All {len(edited_df)} row(s) will be saved (no deletions)")

        st.checkbox(
            "Also push confirmed rows to Google Sheet",
            key="push_gsheet_on_confirm",
            help="CSV save is always done. Enable this only when Sheet secrets are configured. Adds Order and Date columns to preserve extraction sequence.",
        )

        if st.button("✅ Confirm"):
            # Filter out rows marked for deletion
            if "Delete" in edited_df.columns:
                rows_to_delete = edited_df["Delete"].sum() if not edited_df.empty else 0
                final_df = edited_df[edited_df["Delete"] == False].copy()
                # Remove the Delete column from final output
                final_df = final_df.drop(columns=["Delete"])
                
                if rows_to_delete > 0:
                    st.info(f"🗑️ Removed {rows_to_delete} row(s) marked for deletion")
            else:
                final_df = edited_df.copy()
            
            # Add Date column to preserve selected order date
            selected_date = st.session_state.get("active_order_date", date.today()).isoformat()
            final_df["Date"] = selected_date
            
            st.session_state["validated_items"] = final_df
            st.success(f"✅ Validated successfully - {len(final_df)} item(s) confirmed")

            source_file = st.session_state.get("active_source_file", "Unknown_File")
            csv_ok, csv_msg = save_validated_items_to_csv(
                final_df,
                source_file=source_file,
                replace_existing=True,
                target_date=st.session_state.get("active_order_date", date.today()).isoformat(),
                upload_type=st.session_state.get("active_upload_type", ""),
                uploaded_image_path=st.session_state.get("active_uploaded_image_path", ""),
                client_name=st.session_state.get("active_client_name", ""),
            )
            if csv_ok:
                st.info(csv_msg)
            else:
                st.warning(csv_msg)

            if st.session_state.get("push_gsheet_on_confirm", False):
                push_ok, push_msg = push_validated_items_to_google_sheet(
                    final_df,
                    secrets=st.secrets,
                    gspread_module=gspread,
                    credentials_cls=Credentials,
                    target_date=st.session_state.get("active_order_date", date.today()).isoformat(),
                )
                if push_ok:
                    st.info(push_msg)
                else:
                    st.warning(push_msg)

        if len(st.session_state["validated_items"]):
            st.subheader("✅ Confirmed Output")
            
            # Extract date from validated_items for use in report headers
            validated_items_df = st.session_state["validated_items"]
            order_date_for_export = None
            if "Date" in validated_items_df.columns and not validated_items_df.empty:
                order_date_for_export = validated_items_df["Date"].iloc[0]
            
            confirmed_df = consolidate(validated_items_df)
            st.dataframe(confirmed_df, use_container_width=True)

            # Get short name for reports
            client_full_name = st.session_state.get("active_client_name", "")
            client_short_name = get_client_short_name(client_full_name) if client_full_name else ""
            
            confirmed_excel = export_excel(
                confirmed_df,
                logo_path=get_default_logo_path(),
                header_text="PKS FRESH",
                above_list_text="",
                footer_text="",
                client_name=client_short_name,
                order_date=order_date_for_export,
            )
            confirmed_pdf = export_pdf(
                confirmed_df,
                logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                header_text="PKS FRESH",
                above_list_text="",
                footer_text="",
                client_name=client_short_name,
                order_date=order_date_for_export,
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
                    client_name = ""
                    if "Uploaded Image Path" in selected_df.columns and not selected_df.empty:
                        img_path = str(selected_df["Uploaded Image Path"].iloc[0]).strip()
                    if "Client Name" in selected_df.columns and not selected_df.empty:
                        client_name = str(selected_df["Client Name"].iloc[0]).strip()

                    if client_name:
                        # Convert to short name for display
                        client_short_name = get_client_short_name(client_name)
                        st.info(f"Client Name: {client_short_name}")

                    if selected_saved_date == date.today().isoformat() and img_path and Path(img_path).exists():
                        st.image(img_path, caption=f"Uploaded image: {selected_saved_file}", use_container_width=True)

                    display_cols = [
                        col
                        for col in ["Client Name", "Source Name", "Tamil Name", "Quantity", "Status", "Confidence"]
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
                            client_name=client_name,
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

                    # Get short name for reports
                    client_short_name = get_client_short_name(client_name) if client_name else ""
                    
                    individual_excel = export_excel(
                        individual_df,
                        logo_path=get_default_logo_path(),
                        header_text="PKS FRESH",
                        above_list_text="",
                        footer_text="",
                        client_name=client_short_name,
                        order_date=selected_saved_date,
                    )
                    individual_pdf = export_pdf(
                        individual_df,
                        logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                        header_text="PKS FRESH",
                        above_list_text="",
                        footer_text="",
                        client_name=client_short_name,
                        order_date=selected_saved_date
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
                # Filter options
                st.markdown("### 🔍 Filters")
                
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    # Client filter
                    available_clients = []
                    if "Client Name" in saved_by_date_df.columns:
                        available_clients = [
                            name
                            for name in sorted(saved_by_date_df["Client Name"].astype(str).str.strip().unique().tolist())
                            if name
                        ]
                    
                    if available_clients:
                            selected_clients = st.multiselect(
                                "Select Clients",
                                options=available_clients,
                                default=[],
                                key="filter_clients_consolidated",
                                help="Select which clients to include in consolidation."
                            )
                    else:
                        selected_clients = []
                
                with filter_col2:
                    # Item filter
                    available_items = []
                    if "Tamil Name" in saved_by_date_df.columns:
                        available_items = sorted(saved_by_date_df["Tamil Name"].astype(str).str.strip().unique().tolist())
                    
                    if available_items:
                            selected_items = st.multiselect(
                                "Select Items",
                                options=available_items,
                                default=[],
                                key="filter_items_consolidated",
                                help="Select which items to include in consolidation."
                            )
                    else:
                        selected_items = []
                
                # Apply filters
                filtered_df = saved_by_date_df.copy()
                
                if selected_clients and "Client Name" in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df["Client Name"].astype(str).str.strip().isin(selected_clients)]
                
                if selected_items and "Tamil Name" in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df["Tamil Name"].astype(str).str.strip().isin(selected_items)]
                
                # Show filter summary
                if len(filtered_df) != len(saved_by_date_df):
                    st.info(
                        f"📊 Filtered: {len(filtered_df)} rows (from {len(saved_by_date_df)} total) | "
                        f"Clients: {len(selected_clients)}/{len(available_clients)} | "
                        f"Items: {len(selected_items)}/{len(available_items)}"
                    )
                
                if filtered_df.empty:
                    st.warning("No data matches the selected filters. Please adjust your selection.")
                else:
                    include_client_columns = st.checkbox(
                        "Include client-wise columns in consolidated downloads",
                        value=True,
                        key="include_client_columns_consolidated",
                        help="Adds one quantity column per client in consolidated output.",
                    )

                    if include_client_columns:
                        final_df = consolidate_with_client_columns(filtered_df)
                    else:
                        final_df = consolidate(filtered_df)

                    consolidated_clients = []
                    if "Client Name" in filtered_df.columns:
                        # Get full names from CSV and convert to short names
                        full_names = [
                            name
                            for name in sorted(filtered_df["Client Name"].astype(str).str.strip().unique().tolist())
                            if name
                        ]
                        # Convert each full name to short name
                        consolidated_clients = [get_client_short_name(name) for name in full_names]
                    consolidated_client_name = ", ".join(consolidated_clients)

                    if consolidated_client_name:
                        st.info(f"Client Name(s): {consolidated_client_name}")

                    st.dataframe(final_df, use_container_width=True)

                    # Google Sheets push option
                    push_consolidated_checkbox = st.checkbox(
                        "Push consolidated data to Google Sheet",
                        value=False,
                        key="push_consolidated_gsheet",
                        help="Push to 'consolidated' sheet. Transforms data to: Order | Date | ClientName | Item | Unit | Quantity (one row per client per item). Order column preserves extraction sequence. Primary key: Date+ClientName+Item.",
                    )

                    if push_consolidated_checkbox:
                        if st.button("📤 Push to Google Sheets", key="push_consolidated_btn"):
                            push_ok, push_msg = push_consolidated_to_google_sheet(
                                final_df,
                                target_date=selected_records_date,
                                client_names=consolidated_client_name,
                                secrets=st.secrets,
                                gspread_module=gspread,
                                credentials_cls=Credentials,
                            )
                            if push_ok:
                                st.success(push_msg)
                            else:
                                st.error(push_msg)

                    # consolidated_client_name already contains short names (converted earlier)
                    # Use it directly for reports
                    
                    excel_file = export_excel(
                        final_df,
                        logo_path=get_default_logo_path(),
                        header_text="PKS FRESH",
                        above_list_text="",
                        footer_text="",
                        client_name=consolidated_client_name,
                        order_date=selected_records_date,
                    )

                    pdf_file = export_pdf(
                        final_df,
                        logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                        header_text="PKS FRESH",
                        above_list_text="",
                        footer_text="",
                        client_name=consolidated_client_name,
                        order_date=selected_records_date,
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


with tab_challan:
    st.subheader("📄 Delivery Challan")

    challan_dates = list_saved_dates()
    if not challan_dates:
        st.info("Status: No saved orders available for challan generation.")
    else:
        st.info(f"Status: Available dates with orders = {len(challan_dates)}")

    with st.expander("Generate Delivery Challan", expanded=True):
        available_dates = challan_dates

        if not available_dates:
            st.caption("No saved orders yet. Validate and confirm a file first.")
        else:
            selected_challan_date = st.selectbox(
                "Select date",
                options=available_dates,
                key="selected_challan_date_tab",
            )

            saved_by_date_df = load_saved_rows_for_date(selected_challan_date)
            file_count = 0
            if not saved_by_date_df.empty and "Source File" in saved_by_date_df.columns:
                file_count = saved_by_date_df["Source File"].nunique()
            
            st.info(
                f"Status: Date = {selected_challan_date} | Available orders = {file_count}"
            )

            if saved_by_date_df.empty:
                st.caption("No orders found for selected date.")
            else:
                if "Source File" in saved_by_date_df.columns:
                    source_files = sorted(saved_by_date_df["Source File"].astype(str).unique().tolist())
                else:
                    source_files = []

                if source_files:
                    selected_challan_file = st.selectbox(
                        "Select Order",
                        options=source_files,
                        key="individual_challan_file_tab",
                    )

                    selected_df = saved_by_date_df[saved_by_date_df["Source File"] == selected_challan_file].copy()

                    # Extract client name if available
                    client_name = ""
                    if "Client Name" in selected_df.columns and not selected_df.empty:
                        client_name = str(selected_df["Client Name"].iloc[0]).strip()
                    
                    # Convert to short name for display
                    client_display = get_client_short_name(client_name) if client_name else ""

                    st.info(f"Order: {selected_challan_file} | Items: {len(selected_df)}" + (f" | Client: {client_display}" if client_display else ""))

                    # Challan details input
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        invoice_no = st.text_input("Invoice No.", value="20689", key="challan_invoice_no")
                        po_date = st.text_input("PO Date", value="29-07-2026", key="challan_po_date")
                        vehicle_number = st.text_input("Vehicle Number", value="TN23C P8348", key="challan_vehicle")
                    
                    with col2:
                        invoice_date = st.text_input("Invoice Date", value=date.today().strftime("%d-%m-%Y"), key="challan_invoice_date")
                        po_delivery_date = st.text_input("PO Delivery Date", value=date.today().strftime("%d/%m/%Y"), key="challan_po_delivery")
                        dl_no = st.text_input("DL No.", value="", key="challan_dl_no")
                    
                    with col3:
                        payment_mode = st.selectbox("Payment Mode", options=["Credit", "Cash", "Online Transfer", "Cheque"], key="challan_payment_mode")
                        invoice_amount = st.text_input("Invoice Amount", value="11319.0", key="challan_invoice_amount", help="Total invoice amount")

                    # Address details
                    st.markdown("#### Bill To / Ship To Details")
                    
                    # Load saved addresses
                    saved_addresses = load_addresses()
                    bill_to_options = [addr["name"] for addr in saved_addresses.get("bill_to_addresses", [])]
                    ship_to_options = [addr["name"] for addr in saved_addresses.get("ship_to_addresses", [])]
                    
                    # Add "Add New..." option
                    bill_to_options.append("➕ Add New...")
                    ship_to_options.append("➕ Add New...")
                    
                    col_bill, col_ship = st.columns(2)
                    
                    with col_bill:
                        st.markdown("**Bill To**")
                        
                        # Default to client name if available and exists in options
                        default_bill_idx = 0
                        if client_name and client_name in bill_to_options:
                            default_bill_idx = bill_to_options.index(client_name)
                        
                        bill_to_selection = st.selectbox(
                            "Select Company",
                            options=bill_to_options,
                            index=default_bill_idx,
                            key="challan_bill_to_select"
                        )
                        
                        if bill_to_selection == "➕ Add New...":
                            bill_to_name = st.text_input(
                                "New Company Name",
                                value="",
                                key="challan_bill_to_name_new"
                            )
                            bill_to_address = st.text_area(
                                "Address",
                                value="",
                                height=100,
                                key="challan_bill_to_address_new"
                            )
                            
                            if st.button("💾 Save Bill To Address", key="save_bill_to"):
                                if bill_to_name.strip() and bill_to_address.strip():
                                    if add_bill_to_address(bill_to_name, bill_to_address):
                                        st.success(f"✅ Saved: {bill_to_name}")
                                        st.rerun()
                                    else:
                                        st.warning(f"⚠️ Address already exists: {bill_to_name}")
                                else:
                                    st.warning("⚠️ Please enter both company name and address")
                        else:
                            bill_to_name = bill_to_selection
                            bill_to_address = get_bill_to_address(bill_to_selection)
                            st.text_area(
                                "Address",
                                value=bill_to_address,
                                height=100,
                                disabled=True,
                                key="challan_bill_to_address_display"
                            )
                    
                    with col_ship:
                        st.markdown("**Ship To**")
                        
                        # Default to client name if available and exists in options
                        default_ship_idx = 0
                        if client_name and client_name in ship_to_options:
                            default_ship_idx = ship_to_options.index(client_name)
                        
                        ship_to_selection = st.selectbox(
                            "Select Company",
                            options=ship_to_options,
                            index=default_ship_idx,
                            key="challan_ship_to_select"
                        )
                        
                        if ship_to_selection == "➕ Add New...":
                            ship_to_name = st.text_input(
                                "New Company Name",
                                value="",
                                key="challan_ship_to_name_new"
                            )
                            ship_to_address = st.text_area(
                                "Address",
                                value="",
                                height=100,
                                key="challan_ship_to_address_new"
                            )
                            
                            if st.button("💾 Save Ship To Address", key="save_ship_to"):
                                if ship_to_name.strip() and ship_to_address.strip():
                                    if add_ship_to_address(ship_to_name, ship_to_address):
                                        st.success(f"✅ Saved: {ship_to_name}")
                                        st.rerun()
                                    else:
                                        st.warning(f"⚠️ Address already exists: {ship_to_name}")
                                else:
                                    st.warning("⚠️ Please enter both company name and address")
                        else:
                            ship_to_name = ship_to_selection
                            ship_to_address = get_ship_to_address(ship_to_selection)
                            st.text_area(
                                "Address",
                                value=ship_to_address,
                                height=100,
                                disabled=True,
                                key="challan_ship_to_address_display"
                            )

                    # Company details
                    with st.expander("Company Details (PKS FRESH)", expanded=False):
                        company_col1, company_col2 = st.columns(2)
                        
                        with company_col1:
                            company_name_input = st.text_input("Company Name", value="PKS FRESH", key="challan_company_name")
                            phone_input = st.text_input("Phone", value="9790139595", key="challan_phone")
                        
                        with company_col2:
                            email_input = st.text_input("Email", value="pksfresh1@gmail.com", key="challan_email")
                            company_address_input = st.text_area(
                                "Company Address",
                                value="1971, M.P SARATHI MANSION,\nNETHAJI MARKET,\nCHENNAI,\n652004",
                                height=80,
                                key="challan_company_address"
                            )

                    # Preview items
                    st.markdown("#### Items in Challan")
                    
                    # Sort items alphabetically by Source Name (English name)
                    if "Source Name" in selected_df.columns:
                        selected_df_sorted = selected_df.sort_values(by="Source Name", ascending=True).reset_index(drop=True)
                    else:
                        selected_df_sorted = selected_df.copy()
                    
                    display_cols = [
                        col
                        for col in ["Source Name", "Tamil Name", "Quantity", "Status"]
                        if col in selected_df_sorted.columns
                    ]
                    st.dataframe(selected_df_sorted[display_cols], use_container_width=True)

                    # Generate challans
                    st.markdown("---")
                    
                    challan_excel = export_delivery_challan_excel(
                        selected_df_sorted,
                        invoice_no=invoice_no,
                        invoice_date=invoice_date,
                        po_date=po_date,
                        po_delivery_date=po_delivery_date,
                        vehicle_number=vehicle_number,
                        bill_to_name=bill_to_name,
                        bill_to_address=bill_to_address,
                        ship_to_name=ship_to_name,
                        ship_to_address=ship_to_address,
                        payment_mode=payment_mode,
                        company_name=company_name_input,
                        company_address=company_address_input,
                        phone=phone_input,
                        email=email_input,
                        logo_path=get_default_logo_path(),
                        dl_no=dl_no,
                        invoice_amount=invoice_amount,
                    )

                    challan_pdf = export_delivery_challan_pdf(
                        selected_df_sorted,
                        invoice_no=invoice_no,
                        invoice_date=invoice_date,
                        po_date=po_date,
                        po_delivery_date=po_delivery_date,
                        vehicle_number=vehicle_number,
                        bill_to_name=bill_to_name,
                        bill_to_address=bill_to_address,
                        ship_to_name=ship_to_name,
                        ship_to_address=ship_to_address,
                        payment_mode=payment_mode,
                        company_name=company_name_input,
                        company_address=company_address_input,
                        phone=phone_input,
                        email=email_input,
                        logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                        dl_no=dl_no,
                        invoice_amount=invoice_amount,
                    )

                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        st.download_button(
                            "📥 Download Challan (Excel)",
                            challan_excel,
                            file_name=f"delivery_challan_{invoice_no}_{selected_challan_date}.xlsx",
                            help="Download delivery challan in Excel format"
                        )
                    
                    with col_dl2:
                        st.download_button(
                            "📥 Download Challan (PDF)",
                            challan_pdf,
                            file_name=f"delivery_challan_{invoice_no}_{selected_challan_date}.pdf",
                            help="Download delivery challan in PDF format"
                        )



st.divider()

st.caption(
    "Version 0.2 | OCR + quality review enabled"
)

# Deployment info for debugging
with st.expander("ℹ️ Deployment Info", expanded=False):
    import sys
    import platform
    st.write(f"**Python Version:** {sys.version}")
    st.write(f"**Platform:** {platform.platform()}")
    st.write(f"**Streamlit Version:** {st.__version__}")
    st.write(f"**Working Directory:** {Path.cwd()}")
    
    # Show available features
    features = []
    if pytesseract is not None:
        features.append("✓ Tesseract OCR")
    if gspread is not None:
        features.append("✓ Google Sheets")
    try:
        import paddleocr
        features.append("✓ PaddleOCR")
    except:
        pass
    
    st.write(f"**Available Features:** {', '.join(features) if features else 'None'}")
    
    logger.info("App loaded successfully")