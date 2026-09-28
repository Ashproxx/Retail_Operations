"""Structured, bounded chart specs derived from the same deterministic facts as text."""
from collections import defaultdict
from decimal import Decimal
from app.conversation.analytics import select_rows, grouped, revenue

CATEGORY=['bar','horizontal_bar','pie','doughnut']
TIME=['line','area','bar']
COMPARISON=['grouped_bar','stacked_bar','multi_line','heatmap']


def compatible(group_by, rows):
    if group_by=='date':return TIME
    if group_by=='store_category':return COMPARISON if len({r['store_id'] for r in rows})>1 else CATEGORY
    if group_by=='price_units':return ['scatter'] if any(r.get('unit_price_inr') is not None and r.get('units_sold') is not None for r in rows) else []
    return CATEGORY


def specification(rows,ctx):
    selected=select_rows(rows,ctx)
    if not selected:raise ValueError('No observations are available for this chart.')
    dimension={'category':'normalized_category','family':'apparel_family','store':'store_location','product':'product_label'}.get(ctx.group_by,ctx.group_by)
    allowed=compatible(ctx.group_by,selected)
    if ctx.chart_type not in allowed:raise ValueError('Choose a compatible chart: '+', '.join(allowed))
    common={'type':ctx.chart_type,'metric':ctx.metric,'period':ctx.period,'unit':'INR' if ctx.metric=='revenue' else 'units',
            'title':f"{ctx.metric.title()} · {ctx.location or 'Authorized locations'} · {ctx.period['label']}",
            'fixture':any(r.get('fixture') for r in selected),'sources':sorted({r['source'] for r in selected})}
    if ctx.group_by=='store_category' and len({r['store_id'] for r in selected})>1:
        labels=sorted({r.get('normalized_category') or 'Unknown' for r in selected})
        stores=sorted({r['store_location'] for r in selected})
        datasets=[]
        for store in stores:
            values={x['label']:float(x['value']) for x in grouped([r for r in selected if r['store_location']==store],'normalized_category',ctx.metric)}
            # Absent observations remain null, not zero.
            datasets.append({'label':store,'values':[values.get(label) for label in labels]})
        common.update(labels=labels,datasets=datasets,interpretation='Compare observed contributions across stores. Blank cells mean missing observations, not zero sales.')
    elif ctx.group_by=='price_units':
        products=defaultdict(list)
        for r in selected:products[r['sku_id']].append(r)
        points=[]
        for records in products.values():
            latest=max(records,key=lambda r:r['date'])
            if latest.get('unit_price_inr') is not None:
                points.append({'label':latest['product_label'],'x':float(latest['unit_price_inr']),
                               'y':sum(float(r.get('units_sold') or 0) for r in records)})
        common.update(labels=[],datasets=[],points=points[:100],interpretation='Observed price versus recorded unit sales. Association does not establish price elasticity or causation.')
    else:
        if dimension=='store_category':dimension='normalized_category'
        values=grouped(selected,dimension,ctx.metric)
        if ctx.group_by=='date':values.sort(key=lambda x:x['label'])
        limit=366 if ctx.group_by=='date' else 30
        if len(values)>limit:raise ValueError(f'This chart has more than {limit} groups. Narrow the period or product selection.')
        total=sum(float(x['value']) for x in values)
        strongest=max(values,key=lambda x:float(x['value'])) if values else None
        interpretation=(f"{strongest['label']} has the largest observed {ctx.metric}: {float(strongest['value']):,.2f}"+
                        (f" ({float(strongest['value'])/total*100:.1f}% of this selection)." if total else '.')) if strongest else 'No known metric values.'
        common.update(labels=[x['label'] for x in values],datasets=[{'label':ctx.metric.title(),'values':[float(x['value']) for x in values]}],interpretation=interpretation+' Low sales alone do not establish weak demand; check availability and history.')
    return common
