"""Explicit synthetic development data. Never loaded at application startup."""
import hashlib
from datetime import date,timedelta

def seed(repository):
    snapshots=[{'store_id':sid,'sku_id':'SHIRT-1','observed_on':'2026-09-22','closing_stock':stock,
        'reorder_point':10,'lead_days':3,'daily_demand':4,'source':'synthetic-fixture','fixture':True}
        for sid,stock in [('BANDRA',2),('ANDHERI',3)]]
    repository.add_records('inventory',snapshots,store_names={'BANDRA':'Bandra','ANDHERI':'Andheri'})
    sales=[];analytics=[]
    for i in range(14):
        day=(date(2026,9,9)+timedelta(days=i)).isoformat()
        sales.append({'store_id':'BANDRA','sku_id':'SHIRT-1','day':day,'units':i+1,'source':'synthetic-fixture','fixture':True})
        analytics.append({'store_id':'BANDRA','sku_id':'SHIRT-1','day':day,'category':'shirts','units_sold':i+1,
            'unit_price_inr':'100','closing_stock':2,'reorder_point':10,'source':'synthetic-fixture','fixture':True})
    repository.add_records('demand-forecasting',sales)
    repository.add_records('analytics-reporting',analytics)
    repository.add_records('pricing-promotions',[{'store_id':'BANDRA','sku_id':'SHIRT-1','observed_on':'2026-09-22',
        'current_price':'100','unit_cost':'50','stock_units':20,'promotion_eligible':True,'source':'synthetic-fixture','fixture':True}])
    repository.add_records('supply-chain',[{'store_id':'BANDRA','sku_id':'SHIRT-1','vendor_id':'V1','observed_on':'2026-09-22',
        'promised_lead_days':3,'capacity':100,'unit_cost':'50','source':'synthetic-fixture','fixture':True}])
    repository.add_records('order-fulfillment',[{'store_id':'BANDRA','sku_id':'SHIRT-1','order_id':'O1','quantity':1,'state':'created',
        'placed_at':'2026-09-20T00:00:00Z','updated_at':'2026-09-21T00:00:00Z','promised_at':'2026-09-23T00:00:00Z',
        'source':'synthetic-fixture','fixture':True}])
    repository.add_records('returns-refunds',[{'store_id':'BANDRA','order_id':'O1','observed_on':'2026-09-22',
        'purchased_units':1,'paid_total':'100','refund_status':'requested','source':'synthetic-fixture','fixture':True}])
    text='Customer service FAQ opening hours are nine to five.'
    repository.add_records('customer-service',[{'store_id':'BANDRA','document_id':'FAQ','version':'1',
        'valid_from':'2026-09-01','approved':True,'text':text,'expected_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'source':'synthetic-fixture','fixture':True}])
