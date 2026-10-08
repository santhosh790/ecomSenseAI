import unittest
from unittest.mock import patch

from infrastructure.google_sheets_service import sync_items_count_to_google_sheet


class FakeWorksheet:
    def __init__(self):
        self.rows = []

    def row_values(self, row_number):
        if row_number <= len(self.rows):
            return self.rows[row_number - 1]
        return []

    def get_all_values(self):
        return [row.copy() for row in self.rows]

    def append_row(self, row, value_input_option=None):
        self.rows.append(list(row))

    def append_rows(self, rows, value_input_option=None):
        self.rows.extend([list(row) for row in rows])

    def clear(self):
        self.rows = []

    def update(self, cell_range, rows, value_input_option=None):
        start_index = 0 if cell_range == "A1" else 1
        while len(self.rows) < start_index + len(rows):
            self.rows.append([])
        for offset, row in enumerate(rows):
            self.rows[start_index + offset] = list(row)


class GoogleSheetsMetadataTests(unittest.TestCase):
    def setUp(self):
        self.worksheet = FakeWorksheet()
        self.builder_patch = patch(
            "infrastructure.google_sheets_service._build_google_sheets_client",
            return_value=(self.worksheet, "Orders", ""),
        )
        self.builder_patch.start()
        self.addCleanup(self.builder_patch.stop)

    def sync(self, item_count, **kwargs):
        return sync_items_count_to_google_sheet(
            target_date="2026-10-08",
            source_file="order.pdf",
            client_name="MHS",
            item_count=item_count,
            secrets={},
            gspread_module=None,
            credentials_cls=None,
            **kwargs,
        )

    def test_order_metadata_is_written_once_to_items_count_row(self):
        ok, _ = self.sync(
            2,
            purchase_order_number="MHS/PR/P000476_26-27",
            total_order_value="INR 25,869.00 (Twenty Five Thousand Eight Hundred Sixty Nine Rupees Only)",
        )

        self.assertTrue(ok)
        headers = self.worksheet.rows[0]
        self.assertEqual(len(self.worksheet.rows), 2)
        row = self.worksheet.rows[1]
        self.assertEqual(row[headers.index("Count")], "2")
        self.assertEqual(row[headers.index("PO Number")], "MHS/PR/P000476_26-27")
        self.assertEqual(
            row[headers.index("Total Order Value")],
            "INR 25,869.00 (Twenty Five Thousand Eight Hundred Sixty Nine Rupees Only)",
        )

    def test_replacing_saved_upload_preserves_order_metadata(self):
        self.sync(
            1,
            purchase_order_number="PO-123",
            total_order_value="INR 100.00",
        )

        ok, _ = self.sync(3)

        self.assertTrue(ok)
        headers = self.worksheet.rows[0]
        row = self.worksheet.rows[1]
        self.assertEqual(row[headers.index("PO Number")], "PO-123")
        self.assertEqual(row[headers.index("Total Order Value")], "INR 100.00")


if __name__ == "__main__":
    unittest.main()
