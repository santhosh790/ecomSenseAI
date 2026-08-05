import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd


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


def persist_uploaded_image(uploaded_image_file, target_date=None):
    if uploaded_image_file is None:
        return ""

    date_str = target_date if target_date else date.today().isoformat()
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
    client_name="",
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
    write_df["Client Name"] = str(client_name or "")
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
