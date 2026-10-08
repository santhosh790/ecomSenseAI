import unittest

import pandas as pd

from application.reporting_service import consolidate, merge_saved_order_rows


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
