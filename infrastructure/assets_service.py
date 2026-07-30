import base64
import mimetypes
from pathlib import Path


def bytes_to_data_uri(image_bytes, file_name="logo.png"):
    mime_type = mimetypes.guess_type(file_name)[0] or "image/png"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def get_default_logo_data_uri():
    candidates = [
        Path("assets/pks-logo.jpeg"),
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
        Path("assets/pks-logo.jpeg"),
        Path("assets/PKS_Logo.jpeg"),
        Path("assets/logo.png"),
        Path("assets/logo.jpg"),
        Path("assets/logo.jpeg"),
    ]

    for logo_path in candidates:
        if logo_path.exists():
            return str(logo_path)

    return ""
