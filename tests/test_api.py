import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from api.main import app


class ExtractApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_swagger_docs_are_available_for_browser_testing(self):
        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 200)
        self.assertIn("SwaggerUIBundle", response.text)

    @patch("api.main.extract_total_order_value", return_value="INR 25,869.00")
    @patch("api.main.extract_purchase_order_number", return_value="PO-123")
    @patch(
        "api.main.detect_vegetables",
        return_value=([{"Source Name": "Onion", "Quantity": "2 KG"}], {"extracted_rows": 1}),
    )
    @patch("api.main.read_pdf", return_value="Purchase Order\nPO Number: PO-123")
    def test_extract_pdf_returns_items_and_order_metadata(
        self,
        read_pdf_mock,
        detect_mock,
        po_number_mock,
        total_value_mock,
    ):
        response = self.client.post(
            "/api/v1/extract",
            files={"file": ("order.pdf", b"test pdf", "application/pdf")},
            data={
                "order_date": "2026-10-09",
                "parser_strategy": "VIT",
                "client_name": "Campus Kitchen",
                "confidence_threshold": "80",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["filename"], "order.pdf")
        self.assertEqual(payload["order_date"], "2026-10-09")
        self.assertEqual(payload["parser_strategy"], "VIT")
        self.assertEqual(payload["client_name"], "Campus Kitchen")
        self.assertEqual(payload["purchase_order_number"], "PO-123")
        self.assertEqual(payload["total_order_value"], "INR 25,869.00")
        self.assertEqual(payload["items"][0]["Source Name"], "Onion")
        self.assertEqual(payload["report"]["extracted_rows"], 1)
        detect_mock.assert_called_once()
        self.assertEqual(detect_mock.call_args.kwargs["client_name"], "VIT")
        self.assertEqual(detect_mock.call_args.kwargs["confidence_threshold"], 80)

    def test_unsupported_file_type_is_rejected(self):
        response = self.client.post(
            "/api/v1/extract",
            files={"file": ("order.docx", b"not supported")},
            data={"order_date": "2026-10-09"},
        )

        self.assertEqual(response.status_code, 415)

    def test_confirm_writes_csv_validated_sheet_and_items_count(self):
        with (
            patch("api.main._google_sheet_secrets", return_value={"configured": True}),
            patch("api.main._google_sheet_clients", return_value=(object(), object())),
            patch("api.main.save_validated_items_to_csv", return_value=(True, "csv saved")) as save_csv,
            patch("api.main.push_validated_items_to_google_sheet", return_value=(True, "items saved")) as push_items,
            patch("api.main.sync_items_count_to_google_sheet", return_value=(True, "index saved")) as sync_count,
        ):
            response = self.client.post(
                "/api/v1/orders/confirm",
                json={
                    "order_date": "2026-10-09",
                    "source_file": "order.pdf",
                    "client_name": "Campus Kitchen",
                    "parser_strategy": "VIT",
                    "purchase_order_number": "PO-123",
                    "total_order_value": "INR 1,250.00",
                    "items": [
                        {
                            "Source Name": "Onion",
                            "Tamil Name": "வெங்காயம் (ONION)",
                            "Quantity": "2 KG",
                            "Status": "Auto Extracted",
                        }
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["csv_saved"])
        self.assertTrue(payload["google_sheet_saved"])
        self.assertTrue(payload["items_count_saved"])
        self.assertEqual(payload["item_count"], 1)
        self.assertEqual(save_csv.call_args.kwargs["target_date"], "2026-10-09")
        self.assertEqual(push_items.call_args.kwargs["source_file"], "order.pdf")
        self.assertEqual(sync_count.call_args.kwargs["purchase_order_number"], "PO-123")
        self.assertEqual(sync_count.call_args.kwargs["total_order_value"], "INR 1,250.00")

    @patch("api.main._order_metadata", return_value={"PO Number": "PO-123", "Total Order Value": "INR 100.00"})
    @patch("api.main._order_rows", return_value=pd.DataFrame([{"Source Name": "Onion", "Tamil Name": "வெங்காயம் (ONION)", "Quantity": "2 KG"}]))
    @patch("api.main.consolidate", return_value=pd.DataFrame([{"Tamil Name": "வெங்காயம் (ONION)", "Total Quantity": 2, "Unit": "KG"}]))
    @patch("api.main.export_excel", return_value=b"xlsx-content")
    def test_individual_order_download_returns_excel(self, export_mock, consolidate_mock, rows_mock, metadata_mock):
        response = self.client.get(
            "/api/v1/orders/individual/download",
            params={"order_date": "2026-10-09", "source_file": "order.pdf", "file_format": "xlsx"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"xlsx-content")
        self.assertEqual(metadata_mock.call_args.args, (unittest.mock.ANY, "order.pdf"))
        self.assertEqual(export_mock.call_args.kwargs["purchase_order_number"], "PO-123")

    @patch("api.main.export_excel", return_value=b"consolidated-xlsx")
    @patch("api.main.consolidate", return_value=pd.DataFrame([{"Tamil Name": "வெங்காயம் (ONION)", "Total Quantity": 2, "Unit": "KG"}]))
    @patch("api.main._order_rows", return_value=pd.DataFrame([{"Tamil Name": "வெங்காயம் (ONION)", "Quantity": "2 KG", "Source File": "order.pdf"}]))
    def test_consolidated_download_returns_excel(self, rows_mock, consolidate_mock, export_mock):
        response = self.client.get(
            "/api/v1/orders/consolidated/download",
            params={"order_date": "2026-10-09", "file_format": "xlsx"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"consolidated-xlsx")
        self.assertNotIn("purchase_order_number", export_mock.call_args.kwargs)

    @patch("api.main.export_delivery_challan_excel", return_value=b"challan-xlsx")
    def test_delivery_challan_export(self, export_mock):
        response = self.client.post(
            "/api/v1/delivery-challans/xlsx",
            json={
                "items": [{"Source Name": "Onion", "Tamil Name": "வெங்காயம் (ONION)", "Quantity": "2 KG"}],
                "invoice_no": "INV-1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"challan-xlsx")
        self.assertEqual(export_mock.call_args.kwargs["invoice_no"], "INV-1")


if __name__ == "__main__":
    unittest.main()
