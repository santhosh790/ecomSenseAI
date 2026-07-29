import io
import os
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd


def _configure_macos_weasyprint_loader_paths():
    """Ensure Homebrew dylib paths are visible to WeasyPrint on macOS."""
    if sys.platform != "darwin":
        return

    candidate_dirs = []
    for brew_prefix in (Path("/opt/homebrew"), Path("/usr/local")):
        candidate_dirs.append(brew_prefix / "lib")
        for lib_name in (
            "glib",
            "pango",
            "cairo",
            "gdk-pixbuf",
            "harfbuzz",
            "fontconfig",
            "freetype",
            "libffi",
        ):
            candidate_dirs.append(brew_prefix / "opt" / lib_name / "lib")

    existing_dirs = [str(path) for path in candidate_dirs if path.exists()]
    if not existing_dirs:
        return

    current_paths = [
        path for path in os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "").split(":") if path
    ]
    for path in existing_dirs:
        if path not in current_paths:
            current_paths.append(path)

    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(current_paths)


def _prepare_quantity_fields(df):
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
    return working_df


def consolidate(df):
    if df.empty:
        return df

    working_df = _prepare_quantity_fields(df)

    result = (
        working_df.groupby(["Tamil Name", "Unit"])["Quantity_Value"]
        .sum()
        .reset_index()
    )

    result.rename(columns={"Quantity_Value": "Total Quantity"}, inplace=True)
    return result


def consolidate_with_client_columns(df):
    if df.empty:
        return df

    if "Client Name" not in df.columns:
        return consolidate(df)

    working_df = _prepare_quantity_fields(df)
    working_df["Client Name"] = working_df["Client Name"].astype(str).str.strip()
    working_df["Client Name"] = working_df["Client Name"].replace({"": "Unknown Client"})

    pivot_df = (
        working_df.pivot_table(
            index=["Tamil Name", "Unit"],
            columns="Client Name",
            values="Quantity_Value",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
    )

    client_cols = [col for col in pivot_df.columns if col not in ["Tamil Name", "Unit"]]
    if client_cols:
        pivot_df["Total Quantity"] = pivot_df[client_cols].sum(axis=1)
    else:
        pivot_df["Total Quantity"] = 0.0

    return pivot_df[["Tamil Name", *client_cols, "Total Quantity", "Unit"]]


def export_excel(
    df,
    logo_path="",
    header_text="PKS Fresh",
    above_list_text="காய்கறி பட்டியல்",
    footer_text="",
    client_name="",
):
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Alignment
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    output = io.BytesIO()
    date_str = date.today().strftime("%d-%m-%Y")
    tamil_font_name = "Nirmala UI"
    export_df = df.copy()

    if " " not in export_df.columns:
        export_df[" "] = ""

    client_text = str(client_name or "").strip()
    date_line_text = f"தேதி: {date_str}"
    if client_text:
        date_line_text = f"வாடிக்கையாளர்: {client_text}    |    {date_line_text}"
    if str(above_list_text or "").strip():
        date_line_text = f"{date_line_text}    |    {str(above_list_text)}"

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Vegetables", startrow=6)

        ws = writer.sheets["Vegetables"]

        ws["A1"] = str(header_text or "")
        ws["A3"] = date_line_text

        ws["A1"].font = Font(size=18, bold=True)
        ws["A3"].font = Font(name=tamil_font_name, size=13)

        ws["A1"].alignment = Alignment(horizontal="left")
        ws["A3"].alignment = Alignment(horizontal="left")

        ws.column_dimensions["A"].width = 36
        ws.row_dimensions[3].height = 24

        header_row = 7
        for col_idx in range(1, len(export_df.columns) + 1):
            col_letter = get_column_letter(col_idx)
            ws[f"{col_letter}{header_row}"].font = Font(size=12, bold=True)
            if col_idx > 1 and ws.column_dimensions[col_letter].width is None:
                ws.column_dimensions[col_letter].width = 14

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


def export_pdf(
    df,
    logo_data_uri="",
    header_text="PKS Fresh",
    above_list_text="காய்கறி பட்டியல்",
    footer_text="",
    client_name="",
):
    _configure_macos_weasyprint_loader_paths()
    from weasyprint import HTML

    date_str = date.today().strftime("%d-%m-%Y")
    client_text = str(client_name or "").strip()

    client_cols = [
        col
        for col in df.columns
        if col not in ["Tamil Name", "Total Quantity", "Unit"]
    ]

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

        client_cells = ""
        for col in client_cols:
            value = row.get(col, "")
            try:
                value_num = float(value)
                value_text = f"{value_num:.0f}" if value_num == int(value_num) else f"{value_num:.2f}"
            except (ValueError, TypeError):
                value_text = str(value)
            client_cells += f'<td class="num">{value_text}</td>'

        rows_html += (
            f'<tr style="background:{bg}">'
            f"<td>{i}</td>"
            f"<td><b>{tamil}</b></td>"
            f"{client_cells}"
            f'<td class="num"><b>{qty_str}</b></td>'
            f'<td class="num"><b>{unit}</b></td>'
            "</tr>"
        )

    client_header_html = "".join([f'<th class="num">{col}</th>' for col in client_cols])

    logo_html = ""
    if logo_data_uri:
        logo_html = (
            '<div class="brand-logo-wrap">'
            f'<img class="brand-logo" src="{logo_data_uri}" alt="Company Logo" />'
            "</div>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang=\"ta\">
<head>
<meta charset=\"UTF-8\">
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
    font-size: 16px;
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
    font-size: 16px;
    text-align: left;
  }}
  th.num {{ text-align: right; }}
  td {{
    padding: 8px 14px;
    font-size: 16px;
    border-bottom: 1px solid #ddd;
  }}
  td.num {{ text-align: right; }}
  tfoot td {{
    font-weight: bold;
    border-top: 2px solid #2c3e50;
    padding: 8px 16px;
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
    <div class=\"subtitle\">காய்கறி பட்டியல்</div>
    <div class=\"date-line\">{'வாடிக்கையாளர்: ' + client_text + '  &nbsp;&nbsp; &nbsp;&nbsp;  ' if client_text else ''}{str(above_list_text or '')}  &nbsp;&nbsp; &nbsp;&nbsp;  தேதி: {date_str}</div>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>காய்கறி பெயர்</th>
        {client_header_html}
        <th class=\"num\">அளவு</th>
        <th class=\"num\">அலகு</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
    <tfoot>
      <tr>
                <td colspan=\"2\">மொத்தம் {len(df)} பொருட்கள்</td>
                <td class=\"num\" colspan=\"{len(client_cols) + 2}\"></td>
      </tr>
    </tfoot>
  </table>
    <div class=\"footer-note\">{str(footer_text or '')}</div>
</body>
</html>"""

    output = io.BytesIO()
    HTML(string=html_content).write_pdf(output)
    return output.getvalue()
