"""Authorized canonical observation view over retained imports and legacy records."""
from datetime import date
from decimal import Decimal
import hashlib
import json
from collections import defaultdict
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base
from app.api.schemas import Role
from app.security.policy import authorize, AccessDenied
from app.conversation.taxonomy import normalize


class Observation(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    date: date
    store_id: str = Field(min_length=1, max_length=128)
    store_location: str = Field(min_length=1, max_length=128)
    sku_id: str = Field(min_length=1, max_length=128)
    category: str | None = None
    style_code: str | None = None
    style_name: str | None = None
    gender: str | None = None
    color: str | None = None
    size: str | None = None
    supplier: str | None = None
    unit_price_inr: Decimal = Field(ge=0)
    units_sold: int = Field(ge=0)
    opening_stock: int | None = Field(default=None, ge=0)
    closing_stock: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    vendor_lead_time_days: float | None = Field(default=None, ge=0)
    stockout_risk_flag: bool | None = None


class ObservationRow(Base):
    __tablename__ = 'retail_observations'
    identity: Mapped[str] = mapped_column(String(64), primary_key=True)
    store_id: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON)


def row_key(row):
    return row['store_id'], row['sku_id'], row['date']


def scoped(context, action, store_id=None):
    if context.role == Role.ADMIN or store_id:
        authorize(context, action, store_id)
    else:
        if not context.store_ids: raise AccessDenied('No authorized stores')
        for sid in context.store_ids: authorize(context, action, sid)


class Catalog:
    def __init__(self, runtime, context):
        self.runtime, self.context = runtime, context
        Base.metadata.create_all(runtime.repository.database.engine)

    def observations(self, store_id=None, action='analytics.read'):
        scoped(self.context, action, store_id)
        with self.runtime.repository.database.session() as db:
            q = select(ObservationRow)
            if store_id: q = q.where(ObservationRow.store_id == store_id)
            elif self.context.role != Role.ADMIN: q = q.where(ObservationRow.store_id.in_(self.context.store_ids))
            imported = [r.payload for r in db.scalars(q)]
        names = self.runtime.repository.stores(self.context)
        # Preserve legacy data. Canonical imports take precedence only for exact identities.
        agent = 'inventory' if action == 'inventory.read' else 'demand-forecasting' if action == 'forecast.read' else 'analytics-reporting'
        legacy = self.runtime.repository.records(agent, self.context, store_id)
        rows = []
        for r in legacy:
            rows.append(normalize({'date': r.get('day', r.get('observed_on')), 'store_id': r['store_id'],
                'store_location': names.get(r['store_id'], r['store_id']), 'sku_id': r['sku_id'],
                'category': r.get('category'), 'style_name': None, 'gender': None, 'size': None, 'color': None,
                'supplier': None, 'unit_price_inr': r.get('unit_price_inr'), 'units_sold': r.get('units_sold', r.get('units')),
                'opening_stock': r.get('opening_stock'), 'closing_stock': r.get('closing_stock'),
                'reorder_point': r.get('reorder_point'), 'vendor_lead_time_days': r.get('lead_days'),
                'stockout_risk_flag': r.get('stockout_risk_flag'), 'fixture': r.get('fixture', False), 'source': r['source'], 'raw': r}))
        combined = {row_key(r): r for r in rows}
        combined.update({row_key(r): r for r in imported})
        return list(combined.values())

    def discover(self, dimension, rows, filters=None):
        allowed = {'store_location','normalized_category','apparel_family','gender','size','color','supplier'}
        if dimension not in allowed: raise ValueError('Unsupported discovery dimension')
        filtered = rows
        for field, value in (filters or {}).items():
            filtered = [r for r in filtered if r.get(field) == value]
        return sorted({str(r[dimension]) for r in filtered if r.get(dimension) is not None}, key=str.casefold)

    def products(self, rows):
        latest = {}
        for r in sorted(rows, key=lambda r:r['date']): latest[(r['store_id'],r['sku_id'])] = r
        # One product option per SKU. Ambiguous names receive stable ordinal display suffixes.
        grouped = defaultdict(list)
        products = {}
        for r in latest.values(): products.setdefault(r['sku_id'], r)
        for sku,r in sorted(products.items()): grouped[r['product_label']].append((sku,r))
        result = []
        for label, variants in sorted(grouped.items()):
            for i,(sku,r) in enumerate(variants,1):
                result.append({'value':sku, 'label':label + (f' · variant {i}' if len(variants)>1 else ''),
                    'attributes':{k:r.get(k) for k in ['style_name','category','gender','size','color']}})
        return result

    def product360(self, rows, sku):
        observations = [r for r in rows if r['sku_id'] == sku]
        if not observations: return None
        latest = max(observations, key=lambda r:r['date'])
        return {'label':next(x['label'] for x in self.products(rows) if x['value']==sku),
            'attributes':{k:latest.get(k) for k in ['style_name','apparel_family','normalized_category','gender','color','size','supplier']},
            'observed_through':latest['date'], 'price_inr':latest.get('unit_price_inr'),
            'closing_stock':latest.get('closing_stock'), 'lead_days':latest.get('vendor_lead_time_days'),
            'unknown_attributes':[k for k in ['style_name','gender','color','size','supplier','vendor_lead_time_days'] if latest.get(k) is None]}


def import_observations(database, records, *, source, fixture=False, raw_sources=None):
    """Validate the whole batch before one transaction. Never guess a mapping."""
    prepared = []
    if raw_sources is not None and len(raw_sources) != len(records): raise ValueError('Raw row count mismatch')
    for index, raw in enumerate(records):
        clean = Observation.model_validate(raw).model_dump(mode='json')
        normalized = normalize(clean)
        normalized.update(raw=dict(raw), source=source, fixture=fixture)
        if raw_sources is not None: normalized['raw_source'] = json.loads(json.dumps(raw_sources[index], default=str))
        d = date.fromisoformat(clean['date'])
        normalized.update(weekday=d.weekday(), month=d.month, quarter=(d.month-1)//3+1, year=d.year)
        identity = hashlib.sha256(json.dumps(row_key(clean)).encode()).hexdigest()
        prepared.append(ObservationRow(identity=identity, store_id=clean['store_id'], payload=normalized))
    if len({r.identity for r in prepared}) != len(prepared): raise ValueError('Duplicate store/product/date observations')
    Base.metadata.create_all(database.engine)
    with database.session() as db:
        for row in prepared:
            if db.get(ObservationRow,row.identity): raise ValueError('Existing observations are immutable')
            db.add(row)
    return {'imported':len(prepared),'unmapped_categories':sorted({str(r.payload.get('category')) for r in prepared if r.payload['taxonomy_status']!='mapped'})}
