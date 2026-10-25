from sqlalchemy import String, Integer, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base


class SalesEvent(Base):
    __tablename__='sales_events'
    id: Mapped[int]=mapped_column(primary_key=True)
    txn_id: Mapped[str]=mapped_column(String(128),unique=True)
    store_id: Mapped[str]=mapped_column(String(128),index=True)
    occurred_at: Mapped[str]=mapped_column(String(40),index=True)
    received_at: Mapped[str]=mapped_column(String(40),index=True)
    quantity: Mapped[int]=mapped_column(Integer)
    synthetic: Mapped[bool]=mapped_column(Boolean)
    source: Mapped[str]=mapped_column(String(40))
    digest: Mapped[str]=mapped_column(String(64))
    payload: Mapped[dict]=mapped_column(JSON)


class WeatherHourly(Base):
    __tablename__='weather_hourly'
    __table_args__=(UniqueConstraint('source','observed_at','fetched_at'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    source: Mapped[str]=mapped_column(String(40))
    observed_at: Mapped[str]=mapped_column(String(40),index=True)
    fetched_at: Mapped[str]=mapped_column(String(40),index=True)
    synthetic: Mapped[bool]=mapped_column(Boolean,default=False)
    payload: Mapped[dict]=mapped_column(JSON)
