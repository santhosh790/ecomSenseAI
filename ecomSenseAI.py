import streamlit as st
import pandas as pd
import shutil
from datetime import date
from pathlib import Path

from application.vegetable_detection_service import detect_vegetables as detect_vegetables_service
from application.vegetable_detection_service import find_canonical_vegetable_name as find_canonical_vegetable_name_service
from application.vegetable_catalog_service import load_vegetable_catalog
from application.reporting_service import consolidate, consolidate_with_client_columns, export_excel, export_pdf
from application.extraction_service import normalize_text as normalize_text_service
from infrastructure.assets_service import get_default_logo_data_uri, get_default_logo_path
from infrastructure.document_readers import (
    read_excel,
    read_image,
    read_pdf,
)
from infrastructure.google_sheets_service import push_validated_items_to_google_sheet
from infrastructure.ocr_engine import extract_image_text as extract_image_text_service
from infrastructure.ocr_engine import load_ocr_model
from infrastructure.persistence_service import (
    get_csv_path_for_date,
    list_saved_dates,
    load_saved_rows_for_date,
    load_saved_rows_for_today,
    persist_uploaded_image,
    remove_saved_file_from_csv,
    save_validated_items_to_csv,
)

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

if "download_header_text" not in st.session_state:
    st.session_state["download_header_text"] = "PKS Fresh"

if "download_above_list_text" not in st.session_state:
    st.session_state["download_above_list_text"] = "காய்கறி பட்டியல்"

if "download_footer_text" not in st.session_state:
    st.session_state["download_footer_text"] = ""

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


st.title("🛒 ecomSense AI")
st.subheader(
    "Multilingual Grocery Document Extractor"
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

    st.session_state["active_client_name"] = st.text_input(
        "Client Name",
        value=st.session_state.get("active_client_name", ""),
        help="Enter the actual client name (e.g., 'MRF', 'VIT Canteen'). Saved to CSV for record-keeping.",
        placeholder="Enter client name",
    ).strip()
    
    # Parser selection dropdown
    parser_options = ["Generic", "VIT", "FVIT"]
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
          - Automatically corrects OCR errors (Ko/Ke/Kq → KG)
          - Recommended for most documents
        
        - **VIT**: Optimized for VIT Purchase Orders
          - 11-12 column format
          - Includes item codes (6-7 digits)
          - Pattern: Serial | ItemCode | Material | HSN-UOM-Qty
        
        - **FVIT**: Optimized for FVIT Purchase Orders
          - 8 column format
          - Pattern: Serial | Material | HSN | UOM | Qty
        
        **Tips:**
        - Start with **Generic** - it handles most documents well
        - Switch to VIT/FVIT if Generic doesn't extract properly
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
            help="CSV save is always done. Enable this only when Sheet secrets are configured.",
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
            
            st.session_state["validated_items"] = final_df
            st.success(f"✅ Validated successfully - {len(final_df)} item(s) confirmed")

            source_file = st.session_state.get("active_source_file", "Unknown_File")
            csv_ok, csv_msg = save_validated_items_to_csv(
                final_df,
                source_file=source_file,
                replace_existing=True,
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
                )
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
                client_name=st.session_state.get("active_client_name", ""),
            )
            confirmed_pdf = export_pdf(
                confirmed_df,
                logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                header_text=dl_header,
                above_list_text=dl_above,
                footer_text=dl_footer,
                client_name=st.session_state.get("active_client_name", ""),
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
                        st.info(f"Client Name: {client_name}")

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

                    dl_header, dl_above, dl_footer = get_download_text_customization("individual")

                    individual_excel = export_excel(
                        individual_df,
                        logo_path=get_default_logo_path(),
                        header_text=dl_header,
                        above_list_text=dl_above,
                        footer_text=dl_footer,
                        client_name=client_name,
                    )
                    individual_pdf = export_pdf(
                        individual_df,
                        logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                        header_text=dl_header,
                        above_list_text=dl_above,
                        footer_text=dl_footer,
                        client_name=client_name,
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
                include_client_columns = st.checkbox(
                    "Include client-wise columns in consolidated downloads",
                    value=False,
                    key="include_client_columns_consolidated",
                    help="Adds one quantity column per client in consolidated output.",
                )

                if include_client_columns:
                    final_df = consolidate_with_client_columns(saved_by_date_df)
                else:
                    final_df = consolidate(saved_by_date_df)

                consolidated_clients = []
                if "Client Name" in saved_by_date_df.columns:
                    consolidated_clients = [
                        name
                        for name in sorted(saved_by_date_df["Client Name"].astype(str).str.strip().unique().tolist())
                        if name
                    ]
                consolidated_client_name = ", ".join(consolidated_clients)

                if consolidated_client_name:
                    st.info(f"Client Name(s): {consolidated_client_name}")

                st.dataframe(final_df, use_container_width=True)

                dl_header, dl_above, dl_footer = get_download_text_customization("consolidated")

                excel_file = export_excel(
                    final_df,
                    logo_path=get_default_logo_path(),
                    header_text=dl_header,
                    above_list_text=dl_above,
                    footer_text=dl_footer,
                    client_name=consolidated_client_name,
                )

                pdf_file = export_pdf(
                    final_df,
                    logo_data_uri=st.session_state.get("print_logo_data_uri", ""),
                    header_text=dl_header,
                    above_list_text=dl_above,
                    footer_text=dl_footer,
                    client_name=consolidated_client_name,
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