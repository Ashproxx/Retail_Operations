"""Explicit router ID -> domain contract -> authorization mapping."""
from dataclasses import dataclass
from importlib import import_module

@dataclass(frozen=True)
class Entry:
    module: str
    record_name: str
    action: str
    key_fields: tuple[str, ...]

REGISTRY = {
    'inventory': Entry('inventory', 'Snapshot', 'inventory.read', ('store_id','sku_id','observed_on')),
    'demand-forecasting': Entry('forecasting', 'Sale', 'forecast.read', ('store_id','sku_id','day')),
    'analytics-reporting': Entry('analytics', 'Sale', 'analytics.read', ('store_id','sku_id','day')),
    'pricing-promotions': Entry('pricing', 'Price', 'pricing.recommend', ('store_id','sku_id','observed_on')),
    'supply-chain': Entry('supply', 'Vendor', 'supply.read', ('store_id','vendor_id','sku_id','observed_on')),
    'order-fulfillment': Entry('orders', 'Order', 'orders.read', ('store_id','order_id','updated_at')),
    'customer-service': Entry('support', 'Policy', 'support.read', ('store_id','document_id','version')),
    'returns-refunds': Entry('returns', 'ReturnRecord', 'returns.read', ('store_id','order_id','observed_on')),
}

def contracts(agent):
    entry = REGISTRY[agent]
    domain = import_module(f'app.agents.{entry.module}.domain')
    adapter = import_module(f'app.agents.{entry.module}.agent').Agent
    return getattr(domain, entry.record_name), domain.Query, adapter
