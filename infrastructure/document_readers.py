import fitz  # PyMuPDF
import pandas as pd
from PIL import Image


def read_pdf(file):
    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text


def read_excel(file):
    return pd.read_excel(file)


def read_image(file):
    return Image.open(file)
