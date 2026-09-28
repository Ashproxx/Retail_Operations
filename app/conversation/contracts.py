"""Client inputs never carry identity, permissions or trusted source provenance."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Turn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(default='', max_length=4000)
    action: Literal['select','sales','inventory','forecast','competition','recommendations','diagnose',
                    'visualize','chart','period','locations','products','compare','reset'] | None = None
    value: str | None = Field(default=None, max_length=200)


class Context(BaseModel):
    model_config = ConfigDict(extra='forbid')
    intent: str | None = None
    location: str | None = None
    store_id: str | None = None
    country: str = 'IN'
    timezone: str = 'Asia/Kolkata'
    period: dict | None = None
    comparison_period: dict | None = None
    metric: str = 'revenue'
    category: str | None = None
    product: str | None = None
    sku_id: str | None = None
    gender: str | None = None
    size: str | None = None
    color: str | None = None
    horizon: int = Field(default=7, ge=1, le=90)
    chart_type: str | None = None
    pending: str | None = None
    group_by: str = 'category'
    previous_intent: str | None = None
