"""Observed snapshots and deterministic inventory recommendations."""
from datetime import date
from math import ceil, sqrt
from typing import Literal, Protocol
from pydantic import Field, model_validator
from app.api.schemas import Contract

class Snapshot(Contract):
    store_id: str = Field(min_length=1)
    sku_id: str = Field(min_length=1)
    observed_on: date
    closing_stock: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    lead_days: float = Field(ge=0)
    daily_demand: float | None = Field(default=None, ge=0)
    demand_std: float | None = Field(default=None, ge=0)
    opening_stock: int | None = Field(default=None, ge=0)
    on_order: int = Field(default=0, ge=0)
    reserved: int = Field(default=0, ge=0)
    source: str = Field(min_length=1)
    fixture: bool = False
    @model_validator(mode='after')
    def reservations(self):
        if self.reserved > self.closing_stock: raise ValueError('Reservations exceed stock')
        return self

class Query(Contract):
    action: Literal['summary','low_stock','stockout_risk','overstock'] = 'summary'
    store_id: str | None = None
    sku_id: str | None = None
    as_of: date
    review_days: float = Field(default=7, ge=0, le=365)
    service_z: float = Field(default=1.645, ge=0, le=4)
    overstock_factor: float = Field(default=2, gt=1)

class AllocationStrategy(Protocol):
    def allocate(self, requirements: dict[str,int], capacities: dict[str,int]) -> dict[str,int]: ...

class BayesianDemandStrategy(Protocol):
    def estimate(self, observations: list[float]) -> dict: ...


def analyze(row: Snapshot, query: Query) -> dict:
    available = row.closing_stock-row.reserved
    position = available+row.on_order
    safety = None if row.demand_std is None else query.service_z*row.demand_std*sqrt(row.lead_days)
    demand = row.daily_demand
    target = None if demand is None else ceil(demand*(row.lead_days+query.review_days)+(safety or 0))
    warnings=[]
    if demand is None: warnings.append('Demand missing; no lead-time risk or demand-based recommendation.')
    if row.demand_std is None: warnings.append('Demand variability missing; target omits safety stock.')
    return dict(store_id=row.store_id,sku_id=row.sku_id,observed_on=row.observed_on.isoformat(),
        source=row.source,fixture=row.fixture,available_stock=available,inventory_position=position,
        below_reorder_point=available<row.reorder_point,stockout=available==0,
        days_of_cover=None if not demand else available/demand,
        stockout_risk=None if demand is None else available<demand*row.lead_days,
        safety_stock=safety,computed_reorder_point=None if demand is None else ceil(demand*row.lead_days+(safety or 0)),
        recommended_quantity=None if target is None else max(0,target-position),
        overstock=None if target is None else available>query.overstock_factor*target,
        stock_movement=None if row.opening_stock is None else row.closing_stock-row.opening_stock,
        age_days=(query.as_of-row.observed_on).days,warnings=warnings)


def evaluate(rows: list[Snapshot], query: Query) -> dict:
    latest={};seen=set()
    for row in rows:
        key=(row.store_id,row.sku_id,row.observed_on)
        if key in seen: raise ValueError('Duplicate store/SKU/date snapshot')
        seen.add(key)
        if row.observed_on>query.as_of:continue
        if query.store_id is not None and row.store_id!=query.store_id:continue
        if query.sku_id is not None and row.sku_id!=query.sku_id:continue
        pair=key[:2]
        if pair not in latest or row.observed_on>latest[pair].observed_on:latest[pair]=row
    results=[analyze(latest[k],query) for k in sorted(latest)]
    filters={'low_stock':'below_reorder_point','stockout_risk':'stockout_risk','overstock':'overstock'}
    if query.action in filters:results=[r for r in results if r[filters[query.action]] is True]
    stores={}
    for row in latest.values():
        stores[row.store_id]=stores.get(row.store_id,0)+row.closing_stock-row.reserved
    return {'status':'success' if latest else 'not_found','items':results,'store_available_totals':stores,
            'observed_skus':len(latest),'as_of':query.as_of.isoformat(),
            'assumptions':['Independent daily demand, fixed lead time, normal safety-stock approximation.',
                           'On-order stock is used for order quantity, not assumed available before lead time.',
                           'Stock movement is net opening-to-closing change, not inferred sales.']}
