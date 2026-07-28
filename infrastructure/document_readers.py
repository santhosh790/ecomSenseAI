import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
import re


def _get_file_bytes(file):
    if hasattr(file, "getvalue"):
        return file.getvalue()
    return file.read()


def read_pdf(file):
    text = ""
    pdf = fitz.open(stream=_get_file_bytes(file), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text


def read_pdf_tables(file, max_pages=3, max_tables=5):
    tables = []
    pdf = fitz.open(stream=_get_file_bytes(file), filetype="pdf")

    for page in pdf[:max_pages]:
        finder = page.find_tables()
        if not finder or not finder.tables:
            continue

        for table in finder.tables:
            try:
                df = table.to_pandas()
            except Exception:
                continue

            if df is None or df.empty:
                continue

            # Keep only non-empty rows/cols for easier user mapping in UI.
            df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
            if df.empty:
                continue

            tables.append(df)
            if len(tables) >= max_tables:
                return tables

    return tables


def build_pdf_text_from_mapped_table(df, item_column, qty_column, unit_column=None):
    lines = []

    for _, row in df.iterrows():
        item = str(row.get(item_column, "")).strip()
        qty = str(row.get(qty_column, "")).strip()
        unit = ""
        if unit_column and unit_column != "(none)":
            unit = str(row.get(unit_column, "")).strip()

        if not item or item.lower() == "nan":
            continue
        if not qty or qty.lower() == "nan":
            continue

        if unit and unit.lower() != "nan":
            lines.append(f"{item} {qty} {unit}")
        else:
            lines.append(f"{item} {qty}")

    return "\n".join(lines)


def build_pdf_rows_from_mapped_table(df, item_column, qty_column, unit_column=None):
    mapped_rows = []

    for _, row in df.iterrows():
        item = str(row.get(item_column, "")).strip()
        qty_value = str(row.get(qty_column, "")).strip()
        unit = ""
        if unit_column and unit_column != "(none)":
            unit = str(row.get(unit_column, "")).strip()

        if not item or item.lower() == "nan":
            continue
        if not qty_value or qty_value.lower() == "nan":
            continue

        # Skip non-quantity rows like totals/notes even if a value exists.
        qty_candidate = qty_value.replace(",", "")
        if not re.search(r"\d", qty_candidate):
            continue

        mapped_rows.append(
            {
                "item": item,
                "qty": qty_value,
                "unit": unit,
            }
        )

    return mapped_rows


def read_excel(file):
    return pd.read_excel(file)


def read_image(file):
    return Image.open(file)
