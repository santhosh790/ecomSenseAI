from functools import lru_cache
from datetime import date
from enum import Enum
from io import BytesIO
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from application.extraction_service import (
    extract_purchase_order_number,
    extract_total_order_value,
)
from application.reporting_service import (
    consolidate,
    consolidate_with_client_columns,
    export_delivery_challan_excel,
    export_delivery_challan_pdf,
    export_excel,
    export_pdf,
    format_individual_order_summary,
    merge_saved_order_rows,
)
from application.vegetable_detection_service import detect_vegetables
from infrastructure.document_readers import read_excel, read_image, read_pdf
from infrastructure.google_sheets_service import (
    load_items_count_rows_from_google_sheet,
    load_validated_rows_from_google_sheet,
    push_validated_items_to_google_sheet,
    sync_items_count_to_google_sheet,
)
from infrastructure.ocr_engine import extract_image_text, load_ocr_model
from infrastructure.persistence_service import (
    load_saved_rows_for_date,
    save_validated_items_to_csv,
)


MAX_UPLOAD_SIZE = 20 * 1024 * 1024
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


class ParserStrategy(str, Enum):
    GENERIC = "Generic"
    VIT = "VIT"
    FVIT = "FVIT"
    MHS = "MHS"


class ExtractResponse(BaseModel):
    filename: str
    order_date: date
    parser_strategy: ParserStrategy
    client_name: str
    extracted_text: str
    purchase_order_number: str
    total_order_value: str
    items: list[dict[str, Any]]
    report: dict[str, Any]


class ConfirmOrderRequest(BaseModel):
    order_date: date
    source_file: str
    client_name: str = ""
    parser_strategy: ParserStrategy = ParserStrategy.GENERIC
    purchase_order_number: str = ""
    total_order_value: str = ""
    upload_type: str = ""
    items: list[dict[str, Any]]


class ConfirmOrderResponse(BaseModel):
    order_date: date
    source_file: str
    item_count: int
    csv_saved: bool
    google_sheet_saved: bool
    items_count_saved: bool
    messages: list[str]


class DeliveryChallanRequest(BaseModel):
    items: list[dict[str, Any]]
    invoice_no: str = "20689"
    invoice_date: str = ""
    po_date: str = ""
    po_delivery_date: str = ""
    vehicle_number: str = ""
    bill_to_name: str = ""
    bill_to_address: str = ""
    ship_to_name: str = ""
    ship_to_address: str = ""
    payment_mode: str = "Credit"
    company_name: str = "PKS FRESH"
    company_address: str = ""
    phone: str = ""
    email: str = ""
    dl_no: str = ""
    invoice_amount: str = ""


app = FastAPI(
    title="ecomSenseAI API",
    version="1.0.0",
    description="Document extraction API for ecomSenseAI clients.",
)
cors_origins = [
    origin.strip()
    for origin in os.getenv("ECOMSENSE_CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )


def _google_sheet_secrets() -> dict[str, Any] | None:
    spreadsheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    service_account_json = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON", "").strip()
    service_account_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

    credentials_info = None
    if service_account_json:
        try:
            credentials_info = json.loads(service_account_json)
        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=503,
                detail="GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON must contain valid JSON.",
            ) from error
    elif service_account_file:
        try:
            credentials_info = json.loads(Path(service_account_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise HTTPException(
                status_code=503,
                detail="Could not read Google service-account credentials file.",
            ) from error

    if not spreadsheet_id or not credentials_info:
        return None

    return {
        "google_sheet": {
            "spreadsheet_id": spreadsheet_id,
            "worksheet": os.getenv("GOOGLE_SHEET_WORKSHEET", "Sheet1"),
            "service_account": credentials_info,
        }
    }


def _google_sheet_clients():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as error:
        raise HTTPException(
            status_code=503,
            detail="Google Sheets dependencies are unavailable in the API environment.",
        ) from error
    return gspread, Credentials


def _items_dataframe(items: list[dict[str, Any]]) -> pd.DataFrame:
    if not items:
        raise HTTPException(status_code=422, detail="At least one item is required.")
    dataframe = pd.DataFrame(items).fillna("")
    required_columns = {"Source Name", "Tamil Name", "Quantity"}
    if not required_columns.issubset(dataframe.columns):
        missing = sorted(required_columns - set(dataframe.columns))
        raise HTTPException(
            status_code=422,
            detail=f"Items are missing required fields: {', '.join(missing)}.",
        )
    return dataframe


def _validated_sheet_rows(order_date: date) -> pd.DataFrame:
    secrets = _google_sheet_secrets()
    if secrets is None:
        return pd.DataFrame()
    gspread, credentials_cls = _google_sheet_clients()
    dataframe, message = load_validated_rows_from_google_sheet(
        secrets=secrets,
        gspread_module=gspread,
        credentials_cls=credentials_cls,
        target_date=order_date.isoformat(),
    )
    if dataframe is None:
        raise HTTPException(status_code=502, detail=message)
    return dataframe


def _order_rows(order_date: date, source_file: str | None = None) -> pd.DataFrame:
    local_rows = load_saved_rows_for_date(order_date.isoformat())
    if local_rows is None:
        local_rows = pd.DataFrame()

    if source_file and not local_rows.empty and "Source File" in local_rows.columns:
        local_rows = local_rows[
            local_rows["Source File"].astype(str).str.strip() == source_file.strip()
        ].copy()

    sheet_rows = _validated_sheet_rows(order_date)
    if source_file and not sheet_rows.empty and "Source File" in sheet_rows.columns:
        sheet_rows = sheet_rows[
            sheet_rows["Source File"].astype(str).str.strip() == source_file.strip()
        ].copy()

    return merge_saved_order_rows(local_rows, sheet_rows)


def _order_metadata(order_date: date, source_file: str) -> dict[str, str]:
    secrets = _google_sheet_secrets()
    if secrets is None:
        return {"PO Number": "", "Total Order Value": ""}
    gspread, credentials_cls = _google_sheet_clients()
    dataframe, _ = load_items_count_rows_from_google_sheet(
        secrets=secrets,
        gspread_module=gspread,
        credentials_cls=credentials_cls,
        target_date=order_date.isoformat(),
    )
    if dataframe is None or dataframe.empty or "Source File" not in dataframe.columns:
        return {"PO Number": "", "Total Order Value": ""}
    order_rows = dataframe[
        dataframe["Source File"].astype(str).str.strip() == source_file.strip()
    ]
    if order_rows.empty:
        return {"PO Number": "", "Total Order Value": ""}
    row = order_rows.iloc[-1]
    return {
        "PO Number": str(row.get("PO Number", "") or "").strip(),
        "Total Order Value": str(row.get("Total Order Value", "") or "").strip(),
    }


def _download_response(content: bytes, media_type: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@lru_cache(maxsize=1)
def _get_ocr_model():
    return load_ocr_model()


def _extract_text(filename: str, contents: bytes) -> str:
    extension = Path(filename).suffix.lower()
    file_buffer = BytesIO(contents)

    try:
        if extension == ".pdf":
            return read_pdf(file_buffer)
        if extension in IMAGE_EXTENSIONS:
            image = read_image(file_buffer)
            text, error = extract_image_text(image, ocr_model=_get_ocr_model())
            if error:
                raise HTTPException(status_code=422, detail=error)
            return text
        if extension in {".xlsx", ".xls"}:
            dataframe = read_excel(file_buffer)
            return dataframe.to_string(index=False) if not dataframe.empty else ""
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded {extension or 'document'} file.",
        ) from error

    raise HTTPException(
        status_code=415,
        detail="Supported uploads are PDF, Excel, and common image files.",
    )


@app.get("/", tags=["status"])
def root():
    return {
        "name": "ecomSenseAI API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/v1/health", tags=["status"])
def health():
    return {"status": "ok"}


@app.post("/api/v1/extract", response_model=ExtractResponse, tags=["extraction"])
async def extract_document(
    file: UploadFile = File(...),
    order_date: date = Form(...),
    parser_strategy: ParserStrategy = Form(default=ParserStrategy.GENERIC),
    client_name: str = Form(default=""),
    confidence_threshold: int = Form(default=75, ge=0, le=100),
    auto_extract_threshold: int = Form(default=90, ge=0, le=100),
):
    filename = file.filename or "upload"
    contents = await file.read(MAX_UPLOAD_SIZE + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Maximum upload size is 20 MB.")

    text = _extract_text(filename, contents)
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be read from this document.",
        )

    items, report = detect_vegetables(
        text,
        return_details=True,
        confidence_threshold=confidence_threshold,
        auto_extract_threshold=auto_extract_threshold,
        client_name=None if parser_strategy == ParserStrategy.GENERIC else parser_strategy.value,
    )

    return ExtractResponse(
        filename=filename,
        order_date=order_date,
        parser_strategy=parser_strategy,
        client_name=client_name.strip(),
        extracted_text=text,
        purchase_order_number=extract_purchase_order_number(text),
        total_order_value=extract_total_order_value(text),
        items=items,
        report=report,
    )


@app.get("/api/v1/orders", tags=["orders"])
def list_orders(order_date: date = Query(...)):
    rows = _order_rows(order_date)
    if rows.empty or "Source File" not in rows.columns:
        return {"order_date": order_date, "orders": []}

    group_columns = ["Source File"]
    if "Client Name" in rows.columns:
        group_columns.append("Client Name")
    orders = []
    for keys, order_rows in rows.groupby(group_columns, dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        order = dict(zip(group_columns, [str(value or "") for value in keys]))
        order["item_count"] = int(len(order_rows))
        orders.append(order)
    return {"order_date": order_date, "orders": orders}


@app.post("/api/v1/orders/confirm", response_model=ConfirmOrderResponse, tags=["orders"])
def confirm_order(request: ConfirmOrderRequest):
    source_file = request.source_file.strip()
    if not source_file:
        raise HTTPException(status_code=422, detail="source_file is required.")

    secrets = _google_sheet_secrets()
    if secrets is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Google Sheets are not configured. Set GOOGLE_SHEET_ID and either "
                "GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS."
            ),
        )
    gspread, credentials_cls = _google_sheet_clients()
    items_df = _items_dataframe(request.items)
    items_df["Parser Strategy"] = request.parser_strategy.value

    csv_ok, csv_message = save_validated_items_to_csv(
        items_df,
        source_file=source_file,
        replace_existing=True,
        target_date=request.order_date.isoformat(),
        upload_type=request.upload_type,
        client_name=request.client_name,
    )
    if not csv_ok:
        raise HTTPException(status_code=422, detail=csv_message)

    sheet_ok, sheet_message = push_validated_items_to_google_sheet(
        items_df,
        secrets=secrets,
        gspread_module=gspread,
        credentials_cls=credentials_cls,
        target_date=request.order_date.isoformat(),
        source_file=source_file,
        client_name=request.client_name,
        replace_existing=True,
    )

    items_count_ok = False
    messages = [csv_message, sheet_message]
    if sheet_ok:
        items_count_ok, count_message = sync_items_count_to_google_sheet(
            target_date=request.order_date.isoformat(),
            source_file=source_file,
            client_name=request.client_name,
            item_count=len(items_df),
            secrets=secrets,
            gspread_module=gspread,
            credentials_cls=credentials_cls,
            purchase_order_number=request.purchase_order_number,
            total_order_value=request.total_order_value,
        )
        messages.append(count_message)

    return ConfirmOrderResponse(
        order_date=request.order_date,
        source_file=source_file,
        item_count=len(items_df),
        csv_saved=True,
        google_sheet_saved=sheet_ok,
        items_count_saved=items_count_ok,
        messages=messages,
    )


@app.get("/api/v1/orders/individual/download", tags=["downloads"])
def download_individual_order(
    order_date: date = Query(...),
    source_file: str = Query(...),
    file_format: str = Query(default="xlsx", pattern="^(xlsx|pdf)$"),
    client_name: str = Query(default=""),
):
    rows = _order_rows(order_date, source_file)
    if client_name and "Client Name" in rows.columns:
        rows = rows[rows["Client Name"].astype(str).str.strip() == client_name.strip()].copy()
    if rows.empty:
        raise HTTPException(status_code=404, detail="No saved rows found for this order.")

    metadata = _order_metadata(order_date, source_file)
    client_value = client_name.strip()
    if not client_value and "Client Name" in rows.columns:
        client_value = str(rows["Client Name"].iloc[0]).strip()
    client_short_name = client_value
    total_df = consolidate(rows)
    summary = format_individual_order_summary(total_df, metadata["Total Order Value"])
    order_stub = Path(source_file).stem.replace(" ", "_")

    if file_format == "pdf":
        content = export_pdf(
            total_df,
            header_text="PKS FRESH",
            above_list_text="",
            client_name=client_short_name,
            order_date=order_date.isoformat(),
            purchase_order_number=metadata["PO Number"],
            total_order_value=metadata["Total Order Value"],
            order_totals_summary=summary,
        )
        return _download_response(content, "application/pdf", f"{order_stub}_{order_date}.pdf")

    content = export_excel(
        total_df,
        header_text="PKS FRESH",
        above_list_text="",
        footer_text=summary,
        client_name=client_short_name,
        order_date=order_date.isoformat(),
        purchase_order_number=metadata["PO Number"],
        total_order_value=metadata["Total Order Value"],
    )
    return _download_response(
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"{order_stub}_{order_date}.xlsx",
    )


@app.get("/api/v1/orders/consolidated/download", tags=["downloads"])
def download_consolidated_orders(
    order_date: date = Query(...),
    file_format: str = Query(default="xlsx", pattern="^(xlsx|pdf)$"),
    client_name: str = Query(default=""),
    include_client_columns: bool = Query(default=False),
):
    rows = _order_rows(order_date)
    if client_name and "Client Name" in rows.columns:
        rows = rows[rows["Client Name"].astype(str).str.strip() == client_name.strip()].copy()
    if rows.empty:
        raise HTTPException(status_code=404, detail="No saved rows found for this date.")

    if include_client_columns:
        consolidated_df = consolidate_with_client_columns(rows)
    else:
        consolidated_df = consolidate(rows)
    client_label = client_name.strip()
    if not client_label and "Client Name" in rows.columns:
        client_label = ", ".join(
            sorted(name for name in rows["Client Name"].astype(str).str.strip().unique() if name)
        )

    if file_format == "pdf":
        content = export_pdf(
            consolidated_df,
            header_text="PKS FRESH",
            above_list_text="",
            client_name=client_label,
            order_date=order_date.isoformat(),
        )
        return _download_response(content, "application/pdf", f"consolidated_{order_date}.pdf")

    content = export_excel(
        consolidated_df,
        header_text="PKS FRESH",
        above_list_text="",
        client_name=client_label,
        order_date=order_date.isoformat(),
    )
    return _download_response(
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"consolidated_{order_date}.xlsx",
    )


@app.post("/api/v1/delivery-challans/{file_format}", tags=["delivery challan"])
def create_delivery_challan(file_format: str, request: DeliveryChallanRequest):
    if file_format not in {"xlsx", "pdf"}:
        raise HTTPException(status_code=415, detail="file_format must be 'xlsx' or 'pdf'.")
    items_df = _items_dataframe(request.items)
    values = request.model_dump(exclude={"items"})
    if file_format == "pdf":
        content = export_delivery_challan_pdf(items_df, **values)
        return _download_response(content, "application/pdf", f"challan_{request.invoice_no}.pdf")

    content = export_delivery_challan_excel(items_df, **values)
    return _download_response(
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"challan_{request.invoice_no}.xlsx",
    )
