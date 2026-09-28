"""Internal product similarity only. External market facts require configured data."""
import json
from pathlib import Path
from app.conversation.analytics import select_rows, revenue


def compare(rows,ctx,catalog):
    selected=select_rows(rows,ctx)
    if not ctx.sku_id or not selected:
        return {'status':'insufficient_data','summary':'Choose a product with observed data for this period.'}
    origin=max(selected,key=lambda r:r['date'])
    population=select_rows(rows,ctx.model_copy(update={'sku_id':None,'category':None}))
    candidates={r['sku_id'] for r in population if r['sku_id']!=ctx.sku_id}
    config=json.loads((Path(__file__).parent/'config'/'competition.json').read_text())
    weights=config['weights'];results=[]
    for sku in candidates:
        samples=[r for r in population if r['sku_id']==sku]
        other=max(samples,key=lambda r:r['date'])
        if not origin.get('apparel_family') or origin.get('apparel_family')!=other.get('apparel_family'):continue
        score=0;observed=0;factors={}
        for field in ['normalized_category','apparel_family','gender','color']:
            if origin.get(field) is not None and other.get(field) is not None:
                factors[field]=float(origin[field]==other[field]);observed+=weights[field];score+=weights[field]*factors[field]
        first=origin.get('unit_price_inr');second=other.get('unit_price_inr')
        if first is not None and second is not None:
            a,b=float(first),float(second)
            factors['price']=1-abs(a-b)/max(a,b) if max(a,b)>0 else 1
            observed+=weights['price'];score+=weights['price']*factors['price']
        stores_a={r['store_id'] for r in selected};stores_b={r['store_id'] for r in samples}
        factors['store_overlap']=len(stores_a&stores_b)/len(stores_a|stores_b)
        observed+=weights['store_overlap'];score+=weights['store_overlap']*factors['store_overlap']
        product=catalog.product360(population,sku)
        previous=ctx.model_copy(update={'sku_id':sku})
        results.append({'product':product['label'],'sku_id':sku,'similarity_score':round(score/observed*100,1),
            'observed_weight':round(observed,2),'factors':factors,'units':sum(float(r.get('units_sold') or 0) for r in samples),
            'revenue_inr':str(sum((revenue(r) or 0) for r in samples)),
            'price_difference_inr':round(float(second)-float(first),2) if first is not None and second is not None else None,
            'latest_closing_stock':other.get('closing_stock'),'attributes':product['attributes']})
    results.sort(key=lambda x:(-x['similarity_score'],-x['units'],x['product']))
    target_units=sum(float(r.get('units_sold') or 0) for r in selected)
    for r in results:r['outselling_target']=r['units']>target_units
    return {'status':'success','summary':f"Found {len(results)} internal candidates sharing the observed apparel family. {sum(r['outselling_target'] for r in results)} have higher recorded unit sales in this period.",
            'target':catalog.product360(selected,ctx.sku_id),'candidates':results[:10],
            'weights':weights,'external_status':'External market competitor information is not configured yet.',
            'warnings':[config['limitation'],'Scores normalize only observed factors; missing attributes reduce evidence coverage.',
                        'Higher observed sales do not establish customer substitution or explain causation.'],
            'sources':sorted({r['source'] for r in population}),'fixture':any(r.get('fixture') for r in population)}
