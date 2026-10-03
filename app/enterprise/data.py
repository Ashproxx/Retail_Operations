"""Indexed transaction facts; money is integer paise, raw source columns are retained."""
from sqlalchemy import JSON, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base


class ImportBatch(Base):
    __tablename__ = 'poc_imports'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    domain: Mapped[str] = mapped_column(String(20), index=True)
    report: Mapped[dict] = mapped_column(JSON)


class StoreMetadata(Base):
    __tablename__ = 'poc_stores'
    store_id: Mapped[str] = mapped_column(ForeignKey('stores.id'), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class Product(Base):
    __tablename__ = 'retail_products'
    sku_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class Sale(Base):
    __tablename__ = 'sales_transactions'
    txn_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(128), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey('stores.id'), index=True)
    sku_id: Mapped[str] = mapped_column(ForeignKey('retail_products.sku_id'), index=True)
    day: Mapped[str] = mapped_column(String(10), index=True)
    category: Mapped[str] = mapped_column(String(128), index=True)
    channel: Mapped[str] = mapped_column(String(128), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    net_paise: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)


class CompetitorSale(Base):
    __tablename__ = 'competitor_sales'
    __table_args__ = (UniqueConstraint('week','store_id','category','competitor'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    week: Mapped[str] = mapped_column(String(10), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey('stores.id'), index=True)
    category: Mapped[str] = mapped_column(String(128), index=True)
    competitor: Mapped[str] = mapped_column(String(128), index=True)
    units: Mapped[int] = mapped_column(Integer)
    revenue_paise: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
