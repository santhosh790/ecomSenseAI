import unittest

from application.extraction_service import apply_confidence_policy
from application.extraction_service import detect_vegetables
from application.extraction_service import extract_row_fields
from application.extraction_service import extract_row_quantity
from application.extraction_service import fuzzy_match_vegetable_name


VEGETABLE_ALIASES = {
    "ONION": "ONION",
    "TOMATO": "TOMATO",
    "TOMATO COUNTRY": "TOMATO",
    "POTOTO": "POTATO",
    "POTATO": "POTATO",
    "BANANA RAW": "BANANA RAW",
    "BEANS FRENCH": "BEANS FRENCH",
    "CORINDER": "CORIANDER",
    "CORIANDER": "CORIANDER",
    "CURYLEAVE": "CURRY LEAVES",
    "BABY CORN PEELED": "BABY CORN",
    "BABY CORN": "BABY CORN",
    "MANGALORE CUCUMBER": "MANGALORE CUCUMBER",
}

VEGETABLE_TAMIL_MAP = {
    "ONION": "வெங்காயம்",
    "TOMATO": "தக்காளி",
    "POTATO": "உருளைக்கிழங்கு",
    "BANANA RAW": "வாழைக்காய்",
    "BEANS FRENCH": "பிரெஞ்சு பீன்ஸ்",
    "CORIANDER": "கொத்தமல்லி",
    "CURRY LEAVES": "கறிவேப்பிலை",
    "BABY CORN": "பேபி கார்ன்",
    "MANGALORE CUCUMBER": "மங்களூர் வெள்ளரி",
}

NOISE_LINE_PATTERNS = [
    r"^purchase order",
    r"^order no",
]


class ExtractionServiceTests(unittest.TestCase):
    def test_extract_row_fields_table_style(self):
        line = "1 206558 CORINDER_UB_1X1KG KG 45"
        material, qty = extract_row_fields(line)

        self.assertIn("CORINDER", material)
        self.assertEqual(qty, "45 KG")

    def test_fuzzy_match_common_ocr_typo(self):
        matched, score = fuzzy_match_vegetable_name(
            "POTOTO BIG",
            vegetable_aliases=VEGETABLE_ALIASES,
            confidence_threshold=75,
        )
        self.assertEqual(matched, "POTATO")
        self.assertGreaterEqual(score, 75)

    def test_detect_vegetables_line_level(self):
        text = "\n".join(
            [
                "Purchase Order",
                "1 206558 CORINDER_UB_1X1KG KG 45",
                "2 206559 POTOTO_UB_1X1KG KG 20",
                "3 CURYLEAVE 5 KG",
            ]
        )

        items, report = detect_vegetables(
            text,
            vegetable_aliases=VEGETABLE_ALIASES,
            vegetable_tamil_map=VEGETABLE_TAMIL_MAP,
            noise_line_patterns=NOISE_LINE_PATTERNS,
            return_details=True,
            confidence_threshold=70,
        )

        self.assertEqual(len(items), 3)
        self.assertEqual(report["candidate_lines"], 3)

        names = {row["Source Name"] for row in items}
        self.assertIn("Coriander", names)
        self.assertIn("Potato", names)
        self.assertIn("Curry Leaves", names)

    def test_apply_confidence_policy_marks_review(self):
        items = [
            {
                "Source Name": "Potato",
                "Tamil Name": "உருளைக்கிழங்கு",
                "Quantity": "20 KG",
                "Status": "Auto Extracted",
                "Confidence": "74%",
            },
            {
                "Source Name": "Onion",
                "Tamil Name": "வெங்காயம்",
                "Quantity": "",
                "Status": "Auto Extracted",
                "Confidence": "99%",
            },
        ]

        updated = apply_confidence_policy(items, auto_extract_threshold=90)
        self.assertEqual(updated[0]["Status"], "Needs Review")
        self.assertEqual(updated[1]["Status"], "Needs Review")

    def test_extract_row_quantity_prefers_qty_before_unit(self):
        row = "22 1100051 MANGALORE CUCUMBER 132.00 (SOWTHEKAI) 6 Kgs 22.00"
        qty = extract_row_quantity(row)
        self.assertEqual(qty, "6 KG")

    def test_detect_vegetables_pdf_split_row_keeps_quantity(self):
        text = "\n".join(
            [
                "1 1100006 BABY CORN PEELED",
                "1 Kgs 90.00 90.00",
                "22 1100051 MANGALORE CUCUMBER 132.00",
                "(SOWTHEKAI)",
                "6 Kgs 22.00",
            ]
        )

        items, report = detect_vegetables(
            text,
            vegetable_aliases=VEGETABLE_ALIASES,
            vegetable_tamil_map=VEGETABLE_TAMIL_MAP,
            noise_line_patterns=NOISE_LINE_PATTERNS,
            return_details=True,
            confidence_threshold=70,
        )

        self.assertEqual(report["extracted_rows"], 2)

        qty_by_name = {row["Source Name"]: row["Quantity"] for row in items}
        self.assertEqual(qty_by_name.get("Baby Corn"), "1 KG")
        self.assertEqual(qty_by_name.get("Mangalore Cucumber"), "6 KG")

    def test_detect_vegetables_fragmented_pdf_columns(self):
        text = "\n".join(
            [
                "BABY CORN PEELED",
                "1 Kgs",
                "90.00",
                "2",
                "105.00",
                "1100011",
                "BANANA RAW",
                "3 Kgs",
                "35.00",
                "3",
                "330.00",
                "1100016",
                "BEANS FRENCH",
                "6 Kgs",
                "55.00",
            ]
        )

        items, report = detect_vegetables(
            text,
            vegetable_aliases=VEGETABLE_ALIASES,
            vegetable_tamil_map=VEGETABLE_TAMIL_MAP,
            noise_line_patterns=NOISE_LINE_PATTERNS,
            return_details=True,
            confidence_threshold=70,
        )

        qty_by_name = {row["Source Name"]: row["Quantity"] for row in items}
        self.assertEqual(qty_by_name.get("Baby Corn"), "1 KG")
        self.assertEqual(qty_by_name.get("Banana Raw"), "3 KG")
        self.assertEqual(qty_by_name.get("Beans French"), "6 KG")
        self.assertGreaterEqual(report["with_quantity"], 3)

    def test_detect_vegetables_fragmented_pdf_short_chunk(self):
        text = "\n".join(
            [
                "BABY CORN PEELED",
                "1 Kgs",
                "90.00",
                "2",
                "105.00",
                "1100011",
                "BANANA RAW",
                "3 Kgs",
                "35.00",
            ]
        )

        items, report = detect_vegetables(
            text,
            vegetable_aliases=VEGETABLE_ALIASES,
            vegetable_tamil_map=VEGETABLE_TAMIL_MAP,
            noise_line_patterns=NOISE_LINE_PATTERNS,
            return_details=True,
            confidence_threshold=70,
        )

        qty_by_name = {row["Source Name"]: row["Quantity"] for row in items}
        self.assertEqual(qty_by_name.get("Baby Corn"), "1 KG")
        self.assertEqual(qty_by_name.get("Banana Raw"), "3 KG")
        self.assertGreaterEqual(report["with_quantity"], 2)

    def test_detect_vegetables_fragmented_pdf_uom_qty_split(self):
        text = "\n".join(
            [
                "S.No.",
                "Item Code/Description",
                "HSN/SAC",
                "UOM",
                "Qty",
                "Rate",
                "GST Rate",
                "Amount",
                "1",
                "ONION_KG",
                "070310",
                "Kg",
                "200",
                "25.00",
                "0%",
                "5,000.00",
                "2",
                "TOMATO COUNTRY_1X1 KG",
                "070200",
                "Kg",
                "1",
            ]
        )

        items, report = detect_vegetables(
            text,
            vegetable_aliases=VEGETABLE_ALIASES,
            vegetable_tamil_map=VEGETABLE_TAMIL_MAP,
            noise_line_patterns=NOISE_LINE_PATTERNS,
            return_details=True,
            confidence_threshold=70,
        )

        qty_by_name = {row["Source Name"]: row["Quantity"] for row in items}
        self.assertEqual(qty_by_name.get("Onion"), "200 KG")
        self.assertEqual(qty_by_name.get("Tomato"), "1 KG")
        self.assertGreaterEqual(report["with_quantity"], 2)


if __name__ == "__main__":
    unittest.main()
