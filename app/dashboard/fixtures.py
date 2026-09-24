"""Deterministic, explicitly synthetic records for the opt-in showcase only."""
from datetime import date, timedelta
from app.integration.fixtures import seed


def seed_showcase(repository):
    seed(repository)
    products = [('SHIRT-1', 'Shirts', 899), ('DENIM-2', 'Denim', 1899),
                ('TEE-3', 'Essentials', 599), ('DRESS-4', 'Dresses', 2199),
                ('JACKET-5', 'Outerwear', 2999), ('CHINO-6', 'Trousers', 1499)]
    inventories, analytics, demand = [], [], []
    for store_index, store in enumerate(['BANDRA', 'ANDHERI', 'POWAI']):
        for product_index, (sku, category, price) in enumerate(products):
            existing_inventory = sku == 'SHIRT-1' and store in ['BANDRA', 'ANDHERI']
            existing_sales = sku == 'SHIRT-1' and store == 'BANDRA'
            stock = [5, 46, 84, 8, 27, 62][product_index] + store_index * 3
            common = {'store_id': store, 'sku_id': sku, 'source': 'synthetic-showcase', 'fixture': True}
            if not existing_inventory:
                inventories.append({**common, 'observed_on': '2026-09-22', 'closing_stock': stock,
                    'reorder_point': 15, 'lead_days': 3, 'daily_demand': 4 + product_index,
                    'demand_std': 1.5, 'on_order': 0})
            if not existing_sales:
                for offset in range(14):
                    day = (date(2026, 9, 9) + timedelta(days=offset)).isoformat()
                    units = 3 + product_index + store_index + offset % 5
                    analytics.append({**common, 'day': day, 'category': category, 'units_sold': units,
                        'unit_price_inr': str(price), 'closing_stock': stock, 'reorder_point': 15})
                    demand.append({**common, 'day': day, 'units': units})
    repository.add_records('inventory', inventories, store_names={'POWAI': 'Powai'})
    repository.add_records('analytics-reporting', analytics)
    repository.add_records('demand-forecasting', demand)
