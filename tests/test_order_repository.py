import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from infrastructure.database import get_engine, resolve_database_url
from sqlalchemy.engine import make_url
from infrastructure.order_repository import (
    delete_order,
    get_order_metadata,
    list_order_dates,
    load_order_index,
    load_order_rows,
    save_order,
)


class OrderRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_url = f"sqlite:///{Path(self.temp_dir.name) / 'orders.db'}"
        self.order_date = date(2026, 10, 9)

    def tearDown(self):
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        self.temp_dir.cleanup()

    def test_save_replaces_same_date_and_source_atomically(self):
        save_order(
            self.database_url,
            self.order_date,
            "order.pdf",
            [{"Source Name": "Onion", "Quantity": "2 KG"}],
            client_name="Campus Kitchen",
            parser_strategy="VIT",
            purchase_order_number="PO-123",
            total_order_value="INR 100.00",
        )
        save_order(
            self.database_url,
            self.order_date,
            "order.pdf",
            [
                {"Source Name": "Coriander", "Quantity": "1 KG"},
                {"Source Name": "Mint", "Quantity": "1 KG"},
            ],
            client_name="Campus Kitchen",
            parser_strategy="VIT",
            purchase_order_number="PO-123",
            total_order_value="INR 100.00",
        )
        save_order(
            self.database_url,
            date(2026, 10, 10),
            "order.pdf",
            [{"Source Name": "Potato", "Quantity": "3 KG"}],
        )

        rows = load_order_rows(self.database_url, self.order_date, "order.pdf")
        index = load_order_index(self.database_url, self.order_date)
        metadata = get_order_metadata(self.database_url, self.order_date, "order.pdf")

        self.assertEqual(rows["Source Name"].tolist(), ["Coriander", "Mint"])
        self.assertEqual(rows["PO Number"].unique().tolist(), ["PO-123"])
        self.assertEqual(index.iloc[0]["Count"], 2)
        self.assertEqual(metadata["Total Order Value"], "INR 100.00")
        self.assertEqual(list_order_dates(self.database_url), ["2026-10-10", "2026-10-09"])
        self.assertTrue(delete_order(self.database_url, self.order_date, "order.pdf"))
        self.assertEqual(load_order_rows(self.database_url, self.order_date).empty, True)

    def test_database_url_resolution_prefers_environment_value(self):
        with patch.dict("os.environ", {"DATABASE_URL": "postgres://user:pass@host/db"}):
            self.assertEqual(
                resolve_database_url({"database": {"url": "sqlite:///ignored.db"}}),
                "postgresql+psycopg://user:pass@host/db?sslmode=require",
            )

    def test_database_url_is_built_from_secret_fields_with_safe_encoding(self):
        with patch.dict("os.environ", {"DATABASE_URL": ""}):
            resolved_url = resolve_database_url(
                {
                    "database": {
                        "host": "db.example.test",
                        "port": "5432",
                        "database": "postgres",
                        "user": "postgres",
                        "password": "p@ss:/word",
                    }
                }
            )

        parsed_url = make_url(resolved_url)
        self.assertEqual(parsed_url.host, "db.example.test")
        self.assertEqual(parsed_url.port, 5432)
        self.assertEqual(parsed_url.database, "postgres")
        self.assertEqual(parsed_url.username, "postgres")
        self.assertEqual(parsed_url.password, "p@ss:/word")
        self.assertEqual(parsed_url.query["sslmode"], "require")


if __name__ == "__main__":
    unittest.main()
