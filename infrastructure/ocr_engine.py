import shutil

import numpy as np
from PIL import Image, ImageFilter, ImageOps

try:
    import cv2
except ImportError:
    cv2 = None

PaddleOCR = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

if pytesseract is not None:
    tesseract_binary = shutil.which("tesseract")
    if tesseract_binary:
        pytesseract.pytesseract.tesseract_cmd = tesseract_binary


def load_ocr_model():
    global PaddleOCR

    if PaddleOCR is None:
        try:
            from paddleocr import PaddleOCR as PaddleOCRClass
            PaddleOCR = PaddleOCRClass
        except Exception:
            return None

    if PaddleOCR is None:
        return None

    try:
        return PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
        )
    except Exception:
        return None


def preprocess_image(image):
    img = np.array(image.convert("RGB"))

    if cv2 is None:
        gray = ImageOps.grayscale(Image.fromarray(img))
        return np.array(gray)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
    return gray


def perform_paddle_ocr(image, ocr_model=None):
    model = ocr_model or load_ocr_model()
    if model is None:
        return "", "PaddleOCR is not available. Install paddleocr and paddlepaddle to enable OCR."

    processed = preprocess_image(image)

    try:
        result = model.predict(processed)
    except Exception as err:
        return "", f"PaddleOCR failed: {err}"

    lines = []

    for page in result or []:
        if isinstance(page, dict):
            rec_texts = page.get("rec_texts") or page.get("rec_text") or []
            if isinstance(rec_texts, str):
                lines.append(rec_texts)
            else:
                lines.extend([str(x) for x in rec_texts if str(x).strip()])
        elif isinstance(page, list):
            for item in page:
                if isinstance(item, dict) and item.get("rec_text"):
                    lines.append(str(item["rec_text"]))
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    text_candidate = item[1]
                    if isinstance(text_candidate, (list, tuple)) and text_candidate:
                        lines.append(str(text_candidate[0]))

    text = "\n".join([line.strip() for line in lines if str(line).strip()])

    if not text.strip():
        return "", "No text detected in image. Try a clearer image or higher resolution scan."

    return text, ""


def extract_image_text(image, ocr_model=None):
    text, ocr_error = perform_paddle_ocr(image, ocr_model=ocr_model)
    if text:
        return text, ""

    if pytesseract is None:
        return "", ocr_error or "No OCR engine available."

    gray = ImageOps.grayscale(image)
    enhanced = ImageOps.autocontrast(gray)
    sharpened = enhanced.filter(ImageFilter.SHARPEN)

    try:
        text = pytesseract.image_to_string(sharpened)
    except pytesseract.pytesseract.TesseractNotFoundError:
        return "", (
            "Tesseract OCR binary is not installed on this system. "
            "For Streamlit Cloud, add a packages.txt with 'tesseract-ocr'. "
            "For macOS, run: brew install tesseract"
        )
    except pytesseract.pytesseract.TesseractError as err:
        return "", f"Tesseract OCR failed: {err}"

    if not text.strip():
        return "", "No text detected in image. Try a clearer image or higher resolution scan."

    return text, ""
