"""Conservative English bridge. Never silently pick a SKU/order or unknown store."""
import re
from datetime import datetime, timezone
from app.integration.registry import contracts

class Clarification(ValueError):
    pass

ALLOWED={'store_id','sku_id','order_id','as_of','start','end','action','mode','horizon','window','method',
         'alpha','top_n','review_days','service_z','overstock_factor','question','min_coverage','vendor_id',
         'daily_demand','stock_units','coverage_days','disruption_multiplier','discount_pct','min_margin',
         'max_change_pct','promotion_start','promotion_end','units_requested','reason','has_receipt','opened',
         'serial_mismatch','review_count_threshold'}

def extract(message, supplied, stores):
    if not set(supplied)<=ALLOWED:raise Clarification('Unknown query parameters; use the documented domain schema.')
    result=dict(supplied)
    matches={sid for sid,name in stores.items() if any(re.search(r'(?<!\w)'+re.escape(v)+r'(?!\w)',message,re.I) for v in {sid,name})}
    if len(matches)>1:raise Clarification('Select one store, or use a structured query without a store filter for an authorized aggregate.')
    if matches:
        sid=matches.pop()
        if 'store_id' in result and result['store_id']!=sid:raise Clarification('Store in message conflicts with parameters.')
        result['store_id']=sid
    elif re.search(r'\b(?:in|at|about)\s+[a-z][\w-]+',message,re.I) and 'store_id' not in result:
        raise Clarification('Provide a recognized store_id; no store was guessed.')
    for field,pattern in [('sku_id',r'\bsku\s*[:=#]?\s+([\w-]+)'),('order_id',r'\border\s*[:=#]\s*([\w-]+)')]:
        found=re.search(pattern,message,re.I)
        if found and field not in result:result[field]=found.group(1)
    dates=re.findall(r'\b\d{4}-\d{2}-\d{2}\b',message)
    if len(dates)==1:result.setdefault('as_of',dates[0])
    elif len(dates)==2:result.setdefault('start',dates[0]);result.setdefault('end',dates[1])
    elif len(dates)>2:raise Clarification('Specify the requested date range in parameters.')
    if re.search(r'\b(?:yesterday|last week|last month|next week|tomorrow)\b',message,re.I) and not dates and not any(k in supplied for k in ['as_of','start','end','horizon']):
        raise Clarification('Provide explicit dates or a forecast horizon for this relative-time request.')
    return result

def prepare(agent, message, params, rows):
    _,model,_=contracts(agent)
    fields=model.model_fields
    values={k:v for k,v in params.items() if k in fields}
    notes=[]
    now=datetime.now(timezone.utc)
    if 'as_of' in fields and 'as_of' not in values:
        values['as_of']=now.isoformat() if agent=='order-fulfillment' else now.date().isoformat()
        notes.append('as_of defaults to current UTC; observed record dates remain visible.')
    if agent=='inventory' and 'action' not in values:
        text=message.lower()
        values['action']='stockout_risk' if 'risk' in text else 'overstock' if 'overstock' in text else 'low_stock' if re.search(r'\blow\b|below|reorder|replenish',text) else 'summary'
    if agent=='analytics-reporting':
        dates=[r['day'] for r in rows if r['day']<=now.date().isoformat() and (not values.get('sku_id') or r['sku_id']==values['sku_id'])]
        if dates:
            if 'start' not in values:values['start']=min(dates);notes.append('start uses earliest available observation.')
            if 'end' not in values:values['end']=max(dates);notes.append('end uses latest available observation.')
        elif 'start' not in values or 'end' not in values:
            raise Clarification('No sales dates available; supply start and end or ingest sales data.')
    if agent=='customer-service':values.setdefault('question',message)
    if agent=='returns-refunds':
        values.setdefault('mode','refund_status' if 'refund' in message.lower() else 'eligibility')
        if values['mode']=='eligibility' and not {'reason','has_receipt','opened','units_requested'}<=values.keys():
            raise Clarification('Return eligibility requires reason, has_receipt, opened and units_requested.')
    if agent=='supply-chain' and values.get('mode')=='replenish' and not {'daily_demand','stock_units'}<=values.keys():
        raise Clarification('Replenishment requires observed daily_demand and stock_units.')
    missing=[k for k,v in fields.items() if v.is_required() and k not in values]
    if missing:raise Clarification('Provide required parameters: '+', '.join(missing))
    return model.model_validate(values),notes

def routing_text(message):
    """Small, documented English aliases; never consult a model for authority."""
    text=re.sub(r'\bproducts (?:are )?low\b','products low stock',message,flags=re.I)
    text=re.sub(r'\bproducts sold (?:the )?most\b','top products by units sold',text,flags=re.I)
    text=re.sub(r'[.!?]\s*what actions should be considered\??\s*$','',text,flags=re.I)
    return text
