from datetime import date, datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database import Base, get_engine, get_session_factory


class SavedOrderRecord(Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("order_date", "source_file", name="uq_orders_date_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source_file: Mapped[str] = mapped_column(String(512), nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    parser_strategy: Mapped[str] = mapped_column(String(32), default="Generic", nullable=False)
    purchase_order_number: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    total_order_value: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    upload_type: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    uploaded_image_path: Mapped[str] = mapped_column(String(2048), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )
    items: Mapped[list["SavedOrderItemRecord"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="SavedOrderItemRecord.item_order",
    )


class SavedOrderItemRecord(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_order: Mapped[int] = mapped_column(Integer, nullable=False)
    item_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    order: Mapped[SavedOrderRecord] = relationship(back_populates="items")


def _require_database_url(database_url: str | None) -> str:
    if not database_url:
        raise ValueError("DATABASE_URL is not configured.")
    return database_url


def initialize_database(database_url: str):
    from infrastructure import order_repository  # noqa: F401

    Base.metadata.create_all(get_engine(_require_database_url(database_url)))


def save_order(
    database_url: str,
    order_date: date,
    source_file: str,
    items: list[dict[str, Any]],
    client_name: str = "",
    parser_strategy: str = "Generic",
    purchase_order_number: str = "",
    total_order_value: str = "",
    upload_type: str = "",
    uploaded_image_path: str = "",
) -> SavedOrderRecord:
    database_url = _require_database_url(database_url)
    if not source_file.strip():
        raise ValueError("source_file is required.")
    if not items:
        raise ValueError("At least one order item is required.")

    initialize_database(database_url)
    session_factory = get_session_factory(database_url)
    with session_factory.begin() as session:
        order = session.scalar(
            select(SavedOrderRecord).where(
                SavedOrderRecord.order_date == order_date,
                SavedOrderRecord.source_file == source_file.strip(),
            )
        )
        if order is None:
            order = SavedOrderRecord(order_date=order_date, source_file=source_file.strip())
            session.add(order)

        order.client_name = client_name.strip()
        order.parser_strategy = parser_strategy
        order.purchase_order_number = purchase_order_number.strip()
        order.total_order_value = total_order_value.strip()
        order.upload_type = upload_type.strip()
        order.uploaded_image_path = uploaded_image_path.strip()
        order.items.clear()
        order.items.extend(
            SavedOrderItemRecord(item_order=index, item_data=dict(item))
            for index, item in enumerate(items, start=1)
        )
        session.flush()
        order_id = order.id

    with session_factory() as session:
        return session.get(SavedOrderRecord, order_id)


def load_order_rows(
    database_url: str,
    order_date: date,
    source_file: str | None = None,
) -> pd.DataFrame:
    database_url = _require_database_url(database_url)
    initialize_database(database_url)
    session_factory = get_session_factory(database_url)
    query = select(SavedOrderRecord).where(SavedOrderRecord.order_date == order_date)
    if source_file:
        query = query.where(SavedOrderRecord.source_file == source_file.strip())
    query = query.order_by(SavedOrderRecord.source_file)

    rows = []
    with session_factory() as session:
        orders = session.scalars(query).all()
        for order in orders:
            for item in order.items:
                row = dict(item.item_data)
                row.update(
                    {
                        "Date": order.order_date.isoformat(),
                        "Source File": order.source_file,
                        "Client Name": order.client_name,
                        "Parser Strategy": order.parser_strategy,
                        "PO Number": order.purchase_order_number,
                        "Total Order Value": order.total_order_value,
                        "Upload Type": order.upload_type,
                        "Uploaded Image Path": order.uploaded_image_path,
                        "Saved At": order.updated_at.isoformat(),
                        "Order": item.item_order,
                    }
                )
                rows.append(row)
    return pd.DataFrame(rows).fillna("")


def load_order_index(database_url: str, order_date: date) -> pd.DataFrame:
    database_url = _require_database_url(database_url)
    initialize_database(database_url)
    session_factory = get_session_factory(database_url)
    query = (
        select(SavedOrderRecord)
        .where(SavedOrderRecord.order_date == order_date)
        .order_by(SavedOrderRecord.source_file)
    )
    rows = []
    with session_factory() as session:
        for order in session.scalars(query).all():
            rows.append(
                {
                    "Date": order.order_date.isoformat(),
                    "Source File": order.source_file,
                    "Client Name": order.client_name,
                    "Count": len(order.items),
                    "PO Number": order.purchase_order_number,
                    "Total Order Value": order.total_order_value,
                    "Parser Strategy": order.parser_strategy,
                }
            )
    return pd.DataFrame(rows).fillna("")


def list_order_dates(database_url: str) -> list[str]:
    database_url = _require_database_url(database_url)
    initialize_database(database_url)
    session_factory = get_session_factory(database_url)
    query = select(SavedOrderRecord.order_date).distinct().order_by(SavedOrderRecord.order_date.desc())
    with session_factory() as session:
        return [value.isoformat() for value in session.scalars(query).all()]


def get_order_metadata(database_url: str, order_date: date, source_file: str) -> dict[str, str]:
    database_url = _require_database_url(database_url)
    initialize_database(database_url)
    session_factory = get_session_factory(database_url)
    query = select(SavedOrderRecord).where(
        SavedOrderRecord.order_date == order_date,
        SavedOrderRecord.source_file == source_file.strip(),
    )
    with session_factory() as session:
        order = session.scalar(query)
        if order is None:
            return {}
        return {
            "PO Number": order.purchase_order_number,
            "Total Order Value": order.total_order_value,
            "Client Name": order.client_name,
            "Parser Strategy": order.parser_strategy,
        }


def delete_order(database_url: str, order_date: date, source_file: str) -> bool:
    database_url = _require_database_url(database_url)
    initialize_database(database_url)
    session_factory = get_session_factory(database_url)
    query = select(SavedOrderRecord).where(
        SavedOrderRecord.order_date == order_date,
        SavedOrderRecord.source_file == source_file.strip(),
    )
    with session_factory.begin() as session:
        order = session.scalar(query)
        if order is None:
            return False
        session.delete(order)
    return True
