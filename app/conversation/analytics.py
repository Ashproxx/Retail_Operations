"""Decimal-safe observed analytics; associations and recommendations are not causation."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean
from app.conversation.dates import comparison, season


def select_rows(rows, ctx, period=None):
    period = period or ctx.period
    return [r for r in rows if (not ctx.store_id or r['store_id']==ctx.store_id)
            and (not ctx.sku_id or r['sku_id']==ctx.sku_id)
            and (not ctx.categories or r.get('normalized_category') in ctx.categories)
            and (not ctx.category or r.get('normalized_category')==ctx.category or r.get('apparel_family')==ctx.category)
            and all(not getattr(ctx,k,None) or r.get(k)==getattr(ctx,k) for k in ['gender','size','color'])
            and (not period or period['start']<=r['date']<=period['end'])]


def revenue(row):
    if row.get('units_sold') is None or row.get('unit_price_inr') is None: return None
    return Decimal(str(row['unit_price_inr']))*Decimal(str(row['units_sold']))


def grouped(rows, dimension, metric='revenue'):
    totals=defaultdict(Decimal)
    for row in rows:
        value=revenue(row) if metric=='revenue' else None if row.get('units_sold') is None else Decimal(str(row['units_sold']))
        if value is not None:totals[str(row.get(dimension) or 'Unknown')]+=value
    return [{'label':name,'value':str(value)} for name,value in sorted(totals.items(),key=lambda item:(-item[1],item[0]))]


def latest(rows):
    result={}
    for row in sorted(rows,key=lambda r:r['date']):result[(row['store_id'],row['sku_id'])]=row
    return list(result.values())


def statistics(rows):
    known=[r for r in rows if r.get('units_sold') is not None]
    priced=[r for r in known if revenue(r) is not None]
    units=sum(Decimal(str(r['units_sold'])) for r in known)
    rev=sum((revenue(r) for r in priced),Decimal(0))
    snapshots=latest(rows)
    openings=[r['opening_stock'] for r in rows if r.get('opening_stock') is not None]
    return {'units':str(units) if known else None,'revenue_inr':str(rev) if priced else None,
            'products':len({r['sku_id'] for r in known if r['units_sold']>0}),
            'average_selling_price_inr':str(rev/units) if units and len(priced)==len(known) else None,
            'available_stock':sum(r['closing_stock'] for r in snapshots if r.get('closing_stock') is not None),
            'low_stock_items':sum(r.get('closing_stock') is not None and r.get('reorder_point') is not None and r['closing_stock']<r['reorder_point'] for r in snapshots),
            'stockout_observations':sum(r.get('closing_stock')==0 for r in rows),
            'stockout_observation_rate':sum(r.get('closing_stock')==0 for r in rows)/sum(r.get('closing_stock') is not None for r in rows) if any(r.get('closing_stock') is not None for r in rows) else None,
            'sell_through_proxy':float(units)/sum(openings) if len(openings)==len(rows) and sum(openings)>0 else None,
            'missing_price_observations':len(known)-len(priced),'observed_days':len({r['date'] for r in rows})}


def diagnose(rows, ctx):
    current=select_rows(rows,ctx)
    before=select_rows(rows,ctx,ctx.comparison_period or comparison(ctx.period))
    results=[]
    for sku in sorted({r['sku_id'] for r in current}):
        observed=[r for r in current if r['sku_id']==sku]
        prior=[r for r in before if r['sku_id']==sku]
        now_days={r['date'] for r in observed}; prior_days={r['date'] for r in prior}
        now_units=sum(float(r.get('units_sold') or 0) for r in observed)
        prior_units=sum(float(r.get('units_sold') or 0) for r in prior)
        expected=(date.fromisoformat(ctx.period['end'])-date.fromisoformat(ctx.period['start'])).days+1
        prior_period=ctx.comparison_period or comparison(ctx.period)
        expected_prior=(date.fromisoformat(prior_period['end'])-date.fromisoformat(prior_period['start'])).days+1
        change=None
        stores={r['store_id'] for r in observed+prior}
        complete=all(sum(r['store_id']==store and r.get('units_sold') is not None for r in observed)==expected and sum(r['store_id']==store and r.get('units_sold') is not None for r in prior)==expected_prior for store in stores)
        if complete and len(now_days)==expected and len(prior_days)==expected_prior and prior_units>0:
            change=(now_units/len(now_days)/(prior_units/len(prior_days))-1)*100
        constrained=any(r.get('closing_stock')==0 or r.get('stockout_risk_flag') is True for r in observed)
        if constrained:status='STOCK_CONSTRAINED';why='Observed stockouts or stock-risk flags can constrain sales; low sales do not establish low demand.'
        elif change is None:status='INSUFFICIENT_DATA';why='Complete comparable history or a nonzero baseline is unavailable; no decline was inferred.'
        elif change<=-40:status='LOW_SALES';why='Observed daily unit sales are at least 40% below the complete comparison baseline.'
        elif change<=-20:status='DECLINING';why='Observed daily unit sales are at least 20% below the complete comparison baseline.'
        elif change>=20:status='STRONG';why='Observed daily unit sales are at least 20% above the complete comparison baseline.'
        else:status='NORMAL';why='Observed daily unit sales are within 20% of the comparison baseline.'
        result={'sku_id':sku,'label':max(observed,key=lambda r:r['date'])['product_label'],'status':status,
                'units':now_units,'change_pct':change,'explanation':why,'comparison':prior_period,
                'category':observed[0].get('normalized_category'),'observed_days':len(now_days),
                'stock':sum(r.get('closing_stock') or 0 for r in latest(observed)),
                'limitations':['Snapshot stock does not reveal intraday availability or causal demand.']}
        results.append(result)
    return sorted(results,key=lambda r:r['units'])


def recommendations(diagnostics, ctx):
    actions=[]
    for row in diagnostics[:5]:
        if row['status']=='STOCK_CONSTRAINED':
            what='Review replenishment and size availability before considering a promotion.'
        elif row['status'] in ['LOW_SALES','DECLINING'] and row['stock']>0:
            what='Test a targeted display or a small, measured campaign; review margin and price policy before any discount.'
        elif row['status']=='INSUFFICIENT_DATA':
            what='Collect complete comparable sales and availability history before diagnosing demand or changing prices.'
        else:continue
        actions.append({'type':'recommendation','what':what,'why':row['explanation'],'product':row['label'],
                       'location':ctx.location or 'Authorized locations','period':ctx.period,
                       'evidence':{'units':row['units'],'stock':row['stock'],'change_pct':row['change_pct']},
                       'executed':False})
    return actions


def analyze(rows, ctx):
    selected=select_rows(rows,ctx)
    if not selected:
        return {'status':'no_data','summary':'There are no observations for that selection. Missing records are not zero sales.',
                'key_numbers':{},'findings':[],'diagnostics':[],'recommendations':[],'groups':{},'sources':[]}
    numbers=statistics(selected)
    groups={dim:grouped(selected,dim,ctx.metric) for dim in ['store_location','apparel_family','normalized_category','product_label','gender','color','size','date']}
    prior=select_rows(rows,ctx,ctx.comparison_period or comparison(ctx.period))
    prev=statistics(prior)
    # Counts are disclosed; comparisons never silently fill gaps.
    numbers['comparison']=prev
    numbers['comparison_period']=ctx.comparison_period or comparison(ctx.period)
    diag=diagnose(rows,ctx)
    money='unavailable' if numbers['revenue_inr'] is None else f"INR {Decimal(numbers['revenue_inr']):,.2f}"
    summary=f"{ctx.location or 'Authorized locations'} · {ctx.period['label']}: {numbers['units'] if numbers['units'] is not None else 'unknown'} units sold, {money} observed sales across {numbers['products']} selling products."
    finding=[]
    ranked=groups['normalized_category']
    if ranked:finding.append(f"{ranked[0]['label']} has the highest observed {ctx.metric} in this selection; {ranked[-1]['label']} has the lowest. Rank alone is not a low-demand diagnosis.")
    if numbers['stockout_observations']:finding.append('Stockout observations are present. Sales may understate unconstrained demand.')
    if numbers['missing_price_observations']:finding.append('Some observed prices are missing; revenue is a partial total.')
    return {'status':'success','summary':summary,'key_numbers':numbers,'groups':groups,
            'findings':finding,'diagnostics':diag,'recommendations':recommendations(diag,ctx),
            'calendar':season(ctx.period['end']),
            'sources':sorted({r['source'] for r in selected}),'fixture':any(r.get('fixture') for r in selected),
            'warnings':['Revenue is observed units × price, before tax, discounts and refunds unless included in the source.',
                        'Low-sales thresholds are documented heuristics; no causal effect is established.',
                        'Sell-through is an observed-opening-stock proxy, not a replenishment-adjusted rate.']}
