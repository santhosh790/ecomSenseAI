import unittest
from pathlib import Path

import pandas as pd

from application.reporting_service import consolidate, export_pdf, merge_saved_order_rows


class OrderPdfFontTests(unittest.TestCase):
    def test_tamil_font_is_embedded_in_individual_and_consolidated_reports(self):
        import fitz
        from fontTools.ttLib import TTFont

        tamil_name = "தக்காளி வெங்காயம் கொத்தமல்லி"
        font_path = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansTamil-Regular.ttf"
        with TTFont(font_path) as font:
            self.assertTrue(
                {ord(character) for character in tamil_name if not character.isspace()}
                .issubset(font.getBestCmap())
            )
        for client_columns in ({}, {"Campus Kitchen": 2}):
            with self.subTest(client_columns=client_columns):
                rows = pd.DataFrame([
                    {
                        "Tamil Name": tamil_name,
                        "Total Quantity": 2,
                        "Unit": "KG",
                        **client_columns,
                    }
                ])
                content = export_pdf(rows, client_name="வாடிக்கையாளர்")

                with fitz.open(stream=content, filetype="pdf") as document:
                    tamil_fonts = {
                        font[0]
                        for page in document
                        for font in page.get_fonts()
                        if "TamilFont" in font[3]
                    }
                    self.assertTrue(tamil_fonts, "Bundled Tamil font was not embedded")
                    for font_id in tamil_fonts:
                        embedded_font = document.extract_font(font_id)[3]
                        self.assertTrue(embedded_font)
                    for page in document:
                        for span in page.get_texttrace():
                            for character in span["chars"]:
                                self.assertNotEqual(character[1], 0, "PDF contains a missing glyph")


class SavedOrderMergeTests(unittest.TestCase):
    def test_sheet_mirror_is_not_summed_with_local_csv_copy(self):
        local_rows = pd.DataFrame(
            [
                {
                    "Date": "2026-10-08",
                    "Source File": "order.pdf",
                    "Client Name": "MHS",
                    "Tamil Name": "கொத்தமல்லி (CORIANDER)",
                    "Quantity": "1 KG",
                    "Saved At": "2026-10-08 17:56:27",
                }
            ]
        )
        sheet_rows = pd.DataFrame(
            [
                {
                    "Date": "2026-10-08",
                    "Source File": "order.pdf",
                    "Client Name": "MHS",
                    "Tamil Name": "கொத்தமல்லி (CORIANDER)",
                    "Quantity": "1 KG",
                    "Order": 1,
                }
            ]
        )

        merged = merge_saved_order_rows(local_rows, sheet_rows)
        consolidated = consolidate(merged)

        self.assertEqual(len(merged), 1)
        self.assertEqual(consolidated.iloc[0]["Total Quantity"], 1)

    def test_local_only_uploads_and_repeated_sheet_items_are_preserved(self):
        local_rows = pd.DataFrame(
            [
                {
                    "Date": "2026-10-08",
                    "Source File": "local-only.pdf",
                    "Tamil Name": "வெங்காயம் (ONION)",
                    "Quantity": "2 KG",
                }
            ]
        )
        sheet_rows = pd.DataFrame(
            [
                {
                    "Date": "2026-10-08",
                    "Source File": "sheet-order.pdf",
                    "Tamil Name": "கொத்தமல்லி (CORIANDER)",
                    "Quantity": "1 KG",
                    "Order": 1,
                },
                {
                    "Date": "2026-10-08",
                    "Source File": "sheet-order.pdf",
                    "Tamil Name": "கொத்தமல்லி (CORIANDER)",
                    "Quantity": "2 KG",
                    "Order": 2,
                },
            ]
        )

        merged = merge_saved_order_rows(local_rows, sheet_rows)

        self.assertEqual(len(merged), 3)
        totals = consolidate(merged).set_index("Tamil Name")["Total Quantity"].to_dict()
        self.assertEqual(totals["வெங்காயம் (ONION)"], 2)
        self.assertEqual(totals["கொத்தமல்லி (CORIANDER)"], 3)


if __name__ == "__main__":
    unittest.main()
