"""Scoped SQL retail analysis of imported transaction facts, with progressive context."""
from datetime import date,timedelta
from decimal import Decimal
import re
from sqlalchemy import select,func,case
from app.api.schemas import Role,AuditEvent
from app.security.policy import authorize,AccessDenied
from app.integration.repository import StoreRow
from app.enterprise.data import Sale,CompetitorSale,Product,ImportBatch
from app.conversation import dates
from app.conversation.taxonomy import key,mentioned_categories
from app.conversation.forecast import backtest,predict

DIMENSIONS={'product':Sale.sku_id,'category':Sale.category,'date':Sale.day,'location':StoreRow.name,'channel':Sale.channel,
    **{k:Sale.payload[k].as_string() for k in ['style_name','gender','color','size','zone','payment_mode','customer_type','fulfillment_type','time_slot']}}
GROUP_WORDS={'payment':'payment_mode','channel':'channel','website':'channel','style':'style_name','gender':'gender','color':'color','size':'size','zone':'zone','customer':'customer_type','fulfillment':'fulfillment_type','time slot':'time_slot','daily':'date','over time':'date','location':'location','store':'location','category':'category'}
ENTITIES={'product':r'\b(products?|items?|skus?)\b','category':r'\b(categor(?:y|ies))\b','location':r'\b(stores?|locations?)\b','channel':r'\bchannels?\b','style_name':r'\bstyles?\b'}
CHARTS={'pie':'pie','doughnut':'doughnut','donut':'doughnut','horizontal bar':'horizontal_bar','stacked bar':'stacked_bar','grouped bar':'grouped_bar','multi-line':'multi_line','heatmap':'heatmap','scatter':'scatter','area':'area','line':'line','bar':'bar'}


def permits(ctx):
    if ctx.role==Role.ADMIN:authorize(ctx,'analytics.read')
    elif not ctx.store_ids:raise AccessDenied('No authorized stores')
    else:
        for sid in ctx.store_ids:authorize(ctx,'analytics.read',sid)


def filters(ctx,state,model=Sale,period=True):
    permits(ctx);clauses=[]
    if ctx.role!=Role.ADMIN:clauses.append(model.store_id.in_(ctx.store_ids))
    if state.get('store_id'):clauses.append(model.store_id==state['store_id'])
    if state.get('categories'):clauses.append(model.category.in_(state['categories']))
    if period and state.get('period'):
        start,end=state['period']['start'],state['period']['end']
        if model==CompetitorSale:
            start=(date.fromisoformat(start)-timedelta(days=date.fromisoformat(start).weekday())).isoformat()
        clauses.extend([(model.day if model==Sale else model.week)>=start,(model.day if model==Sale else model.week)<=end])
    if model==Sale:
        if state.get('sku_id'):clauses.append(Sale.sku_id==state['sku_id'])
        for field,value in state.get('filters',{}).items():
            if field in DIMENSIONS:clauses.append(DIMENSIONS[field]==value)
    return clauses


class RetailService:
    def __init__(self,runtime):self.runtime=runtime;self.db=runtime.repository.database

    def options(self,ctx):
        clauses=filters(ctx,{})
        with self.db.session() as s:
            stores=s.execute(select(StoreRow.id,StoreRow.name).join(Sale,Sale.store_id==StoreRow.id).where(*clauses).distinct().order_by(StoreRow.name)).all()
            bounds=s.execute(select(func.min(Sale.day),func.max(Sale.day)).where(*clauses)).one()
            dimensions={k:list(s.scalars(select(v).select_from(Sale).join(StoreRow,StoreRow.id==Sale.store_id).where(*clauses,v.is_not(None)).distinct().order_by(v))) for k,v in DIMENSIONS.items() if k!='date'}
            products=[{'value':r.sku_id,'label':' · '.join(str(r.payload.get(k) or '') for k in ['style_name','gender','color','size'])} for r in s.scalars(select(Product).where(Product.sku_id.in_(select(Sale.sku_id).where(*clauses))).order_by(Product.sku_id))]
            competitors=list(s.scalars(select(CompetitorSale.competitor).where(*filters(ctx,{},CompetitorSale)).distinct()))
        return {'locations':[{'label':n,'value':i} for i,n in stores],'dimensions':dimensions,'products':products,'date_range':list(bounds),
            'competitors':competitors,'source':'POC Navi Mumbai Sales Dataset','synthetic':True,'inventory_available':False}

    def run(self,turn,ctx):
        response=None
        try:
            response=self._run(turn,ctx);return response
        finally:
            self.runtime.audit.append(AuditEvent(request_id=ctx.request_id,session_id=ctx.session_id,user_role=ctx.role,actor_id=ctx.principal_id,
                agents_called=['retail-operations'],tools_called=['retail.scoped_sql'],confidence=0,latency_ms=0,final_status=(response or {}).get('status','denied_or_error')))

    def _run(self,turn,ctx):
        opts=self.options(ctx);owner=ctx.model_copy(update={'session_id':'phase3:retail:'+ctx.session_id})
        state=self.runtime.repository.memory(owner) or {'intent':'sales','group':'category','filters':{}}
        if turn.action=='reset':state={'intent':'sales','group':'category','filters':{}}
        text=key(turn.message);stores={p['value']:p['label'] for p in opts['locations']}
        if state.get('store_id') and state['store_id'] not in stores:state.pop('store_id',None);state.pop('location',None)
        def finish(result):
            self.runtime.repository.remember(owner,state)
            return {**result,'context':{k:v for k,v in state.items() if k not in ['store_id','sku_id','pending','last_products']},'synthetic':True,'source':opts['source'],'request_id':str(ctx.request_id),'operational_write_performed':False}
        def ask(field,question,choices):
            state['pending']=field
            return finish({'status':'needs_clarification','summary':question,'choices':choices})
        if re.search(r'\b(employee|salary|attendance|payroll|staffing|human resources)\b',text):
            return finish({'status':'route','summary':'That question belongs to Employee 360. Open that workspace to continue.','workspace':'/employees'})
        if not opts['date_range'][0]:return finish({'status':'no_data','summary':'No authorized sales data is loaded. Import the Navi Mumbai sales workbook.'})
        if turn.action in ['sales','inventory','forecast','competition','delivery']:state['intent']=turn.action
        elif re.search(r'\b(stock|inventory|reorder)\b',text):state['intent']='inventory'
        elif re.search(r'forecast|predict|next \d+ days',text):state['intent']='forecast'
        elif re.search(r'compet|price position|expensive',text) or any(key(n) in text for n in opts['competitors']):state['intent']='competition'
        elif re.search(r'delivery|shipment|shipping|delays',text):state['intent']='delivery'
        elif re.search(r'\b(sales?|revenue|sold|perform|selling|doing|lowest|highest|least|most|best|worst|top|bottom|products?|units?)\b',text):state['intent']='sales'
        if state['intent']=='inventory':return finish({'status':'unavailable','summary':'Current stock data is unavailable. This sales workbook contains no measured on-hand, opening or closing inventory. Sales are not stock balances.','actions':[{'label':'Sales analysis','action':'sales'}]})
        if turn.action=='location':state.pop('location',None);state.pop('store_id',None)
        if turn.action=='period':state.pop('period',None)
        matches=[p for p in opts['locations'] if re.search(r'(?<!\w)'+re.escape(key(p['label']))+r'(?!\w)',text)]
        if len(matches)==1:state.update(store_id=matches[0]['value'],location=matches[0]['label'])
        if len(matches)>1 or re.search(r'all (?:locations|stores)|which (?:location|store)|compare (?:locations|stores)',text):
            state.update(store_id=None,location='All authorized locations',group='location')
        categories=mentioned_categories(text)
        if categories:
            categories=[c for c in categories if c in opts['dimensions']['category']]
            if not categories:return finish({'status':'no_data','summary':'That apparel category has no authorized transaction records.'})
            state['categories']=categories;state.pop('sku_id',None)
        if re.search(r'all (?:products|categories)|clear filters',text):state['categories']=[];state['filters']={};state.pop('sku_id',None)
        for dim in ['channel','gender','color','size','zone','payment_mode','customer_type','fulfillment_type','style_name']:
            found=[v for v in opts['dimensions'][dim] if re.search(r'(?<!\w)'+re.escape(key(v))+r'(?!\w)',text)]
            if len(found)==1:state.setdefault('filters',{})[dim]=found[0]
        for word,dim in GROUP_WORDS.items():
            if re.search(r'\bby '+re.escape(word)+r'|\bcompare '+re.escape(word)+r'|'+('daily|over time' if dim=='date' else r'(?!)'),text):state['group']=dim;break
        if turn.action=='group' and turn.value in DIMENSIONS:state['group']=turn.value
        # Interpret the requested analysis independently from retained scope. No generated SQL or business facts.
        low=re.search(r'\b(lowest|least|worst|bottom|slowest)\b',text)
        high=re.search(r'\b(highest|most|best|top)\b',text)
        entity=next((dim for dim,pattern in ENTITIES.items() if re.search(pattern,text)),None)
        if (low or high) and state['intent']=='sales':
            state['intent']='sales';state['rank']='lowest' if low else 'highest'
            n=re.search(r'\b(?:top|bottom|lowest|highest|best|worst)\s+(\d+)\b',text)
            state['limit']=min(50,max(1,int(n.group(1)))) if n else 1
            if entity:state['group']=entity
            if state['group']=='product':state.pop('sku_id',None)
        elif entity and re.search(r'\b(by|compare|breakdown|each|list|all)\b',text):
            state['group']=entity
            if re.search(r'\b(compare|breakdown|each|list|all)\b',text):state.pop('rank',None)
        elif entity and state.get('rank') and re.search(r'\b(what about|and|instead)\b',text):state['group']=entity
        if re.search(r'\b(units?|quantity|quantities|pieces)\b',text):state['metric']='units'
        elif re.search(r'\b(revenue|value|amount|money)\b',text):state['metric']='net_revenue_inr'
        elif (low or high) and re.search(r'\b(sold|selling)\b',text):state['metric']='units'
        elif re.search(r'\borders?\b',text) and state['intent']=='sales':state['metric']='orders'
        if re.search(r'\b(overall|summary|total sales|all sales)\b',text) or turn.action=='sales':state.pop('rank',None)
        focus=re.search(r'\b(that product|this product|about it|about that|its sales)\b',text)
        if focus:
            candidates=[p for p in opts['products'] if p['value'] in state.get('last_products',[])]
            if len(candidates)!=1:return ask('product','Which product do you mean?',candidates or opts['products'])
            state.update(sku_id=candidates[0]['value'],group='product',intent='sales');state.pop('rank',None)
        period=dates.resolve(turn.message,available=opts['date_range']) if turn.message else None
        if period:state['period']=period
        if 'latest' in text or turn.action=='latest':
            with self.db.session() as s:latest=s.scalar(select(func.max(Sale.day)).where(*filters(ctx,state,period=False)))
            if not latest:return finish({'status':'no_data','summary':'No observations match these filters.'})
            state['period']=dates.resolve(latest)
        if turn.action=='select':
            if state.get('pending')=='location' and (turn.value in stores or turn.value=='*'):
                state.update(store_id=None if turn.value=='*' else turn.value,location='All authorized locations' if turn.value=='*' else stores[turn.value])
            elif state.get('pending')=='period':
                state['period']=dates.resolve(opts['date_range'][1] if turn.value=='latest' else turn.value,available=opts['date_range'])
            elif state.get('pending')=='chart':state['chart']=turn.value
            elif state.get('pending')=='product' and turn.value in {p['value'] for p in opts['products']}:
                state.update(sku_id=turn.value,group='product',intent='sales');state.pop('rank',None)
            else:raise ValueError('Invalid selection')
            state.pop('pending',None)
        if not state.get('location'):return ask('location','Which location would you like to analyse?',opts['locations']+[{'label':'All authorized locations','value':'*'}])
        if not state.get('period'):return ask('period','Which period? The available sales dates are '+ ' to '.join(opts['date_range'])+'.',[{'label':'Latest available day','value':'latest'}]+[{'label':x,'value':x} for x in ['Today','Last 7 days','Last month','Available data']])
        explain=bool(state.get('rank') and re.search(r'\b(why|reason|explain)\b',text))
        recognized=turn.action or period or matches or categories or low or high or focus or explain or entity or any(re.search(r'(?<!\w)'+re.escape(key(v))+r'(?!\w)',text) for values in opts['dimensions'].values() for v in values) or re.search(r'\b(sales?|revenue|sold|selling|perform|doing|units?|quantity|orders?|forecast|predict|compet\w*|delivery|shipment|shipping|delays|latest|chart|graph|bar|line|area|pie|doughnut|donut|heatmap|daily|compare|clear filters|summary|overall)\b',text)
        if text and not recognized:return finish({'status':'needs_clarification','summary':'I could not map that question to a retail analysis. You can ask for a highest/lowest product, compare stores, change the period, or request a chart. Your location and period are still selected.','actions':[{'label':'Sales summary','action':'sales'},{'label':'Change period','action':'period'}]})
        with self.db.session() as s:
            count=s.scalar(select(func.count()).select_from(Sale).where(*filters(ctx,state)))
            latest=s.scalar(select(func.max(Sale.day)).where(*filters(ctx,state,period=False)))
        if not count:return finish({'status':'no_data','summary':f"No sales records are available for {state['period']['label']}. Latest available sales date for this selection is {latest or 'unavailable'}. Missing records are not zero sales.",'actions':[{'label':'Show latest available day','action':'latest'},{'label':'Choose another date','action':'period'}]})
        if state['intent']=='competition':result=self.competition(ctx,state,text)
        elif state['intent']=='delivery':result=self.delivery(ctx,state)
        elif state['intent']=='forecast':result=self.forecast(ctx,state,text)
        else:result=self.sales(ctx,state,explain=explain)
        wants=turn.action=='chart' or 'graph' in text or 'chart' in text or turn.action=='select' and state.get('chart')
        for word,kind in CHARTS.items():
            if re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)',text):state['chart']=kind;wants=True;break
        if turn.action=='chart' and turn.value:state['chart']=turn.value
        if wants and result.get('chart_data'):
            series=result['chart_data'];allowed=['grouped_bar','stacked_bar','multi_line','heatmap'] if series.get('comparison') else ['line','area','bar'] if series.get('time') else ['bar','horizontal_bar','pie','doughnut']
            if state.get('chart') not in allowed:return ask('chart','Which compatible chart would you like?',[{'label':x.replace('_',' ').title(),'value':x} for x in allowed])
            result['visualization']={'type':state['chart'],'title':series['title'],'labels':series['labels'],'datasets':series['datasets'],'interpretation':series['interpretation']}
        result.setdefault('actions',[{'label':label,'action':action} for label,action in [('View graph','chart'),('Change period','period'),('Change location','location'),('Forecast','forecast'),('Competition','competition'),('Delivery','delivery'),('Sales','sales')]])
        result['evidence']={'source':'Sales_Transactions / Competitor_Sales','period':state['period'],'inventory':'Not available','revenue_basis':'Sum of source net_amount_inr, after source discounts; source amounts rounded to whole INR.'}
        return finish(result)

    def sales(self,ctx,state,explain=False):
        clauses=filters(ctx,state);dim=DIMENSIONS[state.get('group','category')]
        with self.db.session() as s:
            total,units,orders=s.execute(select(func.sum(Sale.net_paise),func.sum(Sale.quantity),func.count(func.distinct(Sale.order_id))).where(*clauses)).one()
            grouped=s.execute(select(dim,func.sum(Sale.net_paise),func.sum(Sale.quantity),func.count(func.distinct(Sale.order_id))).select_from(Sale).join(StoreRow,StoreRow.id==Sale.store_id).where(*clauses).group_by(dim).order_by(dim if state.get('group')=='date' else func.sum(Sale.net_paise).desc())).all()
            products={p.sku_id:p.payload for p in s.scalars(select(Product).where(Product.sku_id.in_([r[0] for r in grouped])))} if state['group']=='product' else {}
        labels={sku:' · '.join(str(p[k]) for k in ['style_name','gender','color','size'] if p.get(k)) or sku for sku,p in products.items()}
        rows=[{'group':labels.get(name,name) or 'Not recorded','net_revenue_inr':str(Decimal(money)/100),'units':n,'orders':count} for name,money,n,count in grouped]
        metric=state.get('metric','net_revenue_inr');metric_label={'net_revenue_inr':'net revenue (INR)','units':'units sold','orders':'orders'}[metric]
        rank=state.get('rank');population=len(rows)
        if rank:
            paired=sorted(zip(grouped,rows),key=lambda pair:(Decimal(pair[1][metric])*(1 if rank=='lowest' else -1),str(pair[0][0])))
            boundary=Decimal(paired[min(state.get('limit',1),len(paired))-1][1][metric])
            chosen=[pair for pair in paired if Decimal(pair[1][metric])<=boundary] if rank=='lowest' else [pair for pair in paired if Decimal(pair[1][metric])>=boundary]
            rows=[r for _,r in chosen]
            state['last_products']=[raw[0] for raw,_ in chosen] if state['group']=='product' else []
        elif state['group']=='product':state['last_products']=[raw[0] for raw in grouped]
        best=max(rows,key=lambda r:Decimal(r['net_revenue_inr']));worst=min(rows,key=lambda r:Decimal(r['net_revenue_inr']))
        explanation=f"{best['group']} has the highest recorded net revenue and {worst['group']} the lowest. Low recorded sales alone do not establish weak demand; inventory is unavailable."
        result={'status':'success','summary':f"{state['location']} · {state['period']['label']}: INR {Decimal(total)/100:,.2f} net sales, {units:,} units, {orders:,} orders.",
            'metrics':{'Net sales (INR)':str(Decimal(total)/100),'Units':units,'Orders':orders},'table':rows,'findings':[explanation],
            'chart_data':{'time':state.get('group')=='date','title':'Net sales by '+state.get('group','category').replace('_',' '),'labels':[r['group'] for r in rows],
                'datasets':[{'label':metric_label,'values':[float(r[metric]) for r in rows]}],'interpretation':explanation}}
        result['chart_data']['title']=metric_label.capitalize()+' by '+state['group'].replace('_',' ')
        if state.get('sku_id') and len(rows)==1:result['summary']=rows[0]['group']+'. '+result['summary']
        if rank:
            top=rows[0];value=Decimal(top[metric]);shown=f'INR {value:,.2f}' if metric=='net_revenue_inr' else f'{value:,} {metric_label}'
            subject=state['group'].replace('_',' ')
            result['summary']=(f"{top['group']} had the {rank} {metric_label}: {shown}." if len(rows)==1 else f"{len(rows)} {subject} results with the {rank} {metric_label} are shown below, including ties at the cutoff.")+f" Scope: {state['location']} · {state['period']['label']}."
            result['metrics']={'Matching '+subject+' results':len(rows),'Compared '+subject+' groups':population}
            explanation=f"Ranked by {metric_label} among {population} {subject} groups with recorded transactions. Products without transactions are not assumed to have zero sales. Change the metric by asking ‘by units’ or ‘by revenue’."
            result['findings']=[explanation];result['chart_data']['interpretation']=explanation
            result['actions']=[{'label':'View graph','action':'chart'},{'label':'Change period','action':'period'},{'label':'Change location','action':'location'},{'label':'Sales summary','action':'sales'}]
        if explain:
            result['summary']='The records show the sales outcome, but they do not establish why it happened. '+result['summary']
            result['findings'].append('Price, availability and demand could affect sales, but this workbook does not establish causation or provide inventory balances. Compare units and net revenue across periods before drawing a conclusion.')
        if state.get('group') in ['location','channel'] and not rank and metric in ['net_revenue_inr','units']:
            with self.db.session() as s:
                cells=s.execute(select(dim,Sale.category,func.sum(Sale.net_paise if metric=='net_revenue_inr' else Sale.quantity)).select_from(Sale).join(StoreRow,StoreRow.id==Sale.store_id).where(*clauses).group_by(dim,Sale.category)).all()
            matrix={(label,category):float(Decimal(amount)/(100 if metric=='net_revenue_inr' else 1)) for label,category,amount in cells}
            result['chart_data'].update(comparison=True,datasets=[{'label':category,'values':[matrix.get((r['group'],category)) for r in rows]} for category in sorted({c for _,c,_ in cells})])
        return result

    def delivery(self,ctx,state):
        clauses=filters(ctx,state)+[Sale.payload['fulfillment_type'].as_string()=='Home Delivery']
        with self.db.session() as s:
            orders=select(Sale.order_id,Sale.store_id,func.max(Sale.payload['delay_days_vs_promise'].as_float()).label('delay')).where(*clauses).group_by(Sale.order_id,Sale.store_id).subquery()
            rows=s.execute(select(StoreRow.name,func.count(),func.sum(case((orders.c.delay>0,1),else_=0)),func.avg(orders.c.delay)).select_from(orders).join(StoreRow,StoreRow.id==orders.c.store_id).group_by(StoreRow.name).order_by(func.sum(case((orders.c.delay>0,1),else_=0)).desc())).all()
            statuses=s.execute(select(Sale.payload['delivery_status'].as_string(),func.count(func.distinct(Sale.order_id))).where(*clauses).group_by(Sale.payload['delivery_status'].as_string())).all()
        table=[{'location':name,'home_delivery_orders':n,'delayed_or_overdue_orders':late,'mean_recorded_delay_days':round(avg,2) if avg is not None else None} for name,n,late,avg in rows]
        return {'status':'success','summary':f"{sum(r['home_delivery_orders'] for r in table)} home-delivery orders in this selection. Store pickups are excluded; orders are counted once, not once per line.",'table':table,
            'metrics':{name:n for name,n in statuses},'findings':['Delivery status is the workbook snapshot. Positive recorded delay includes delivered lateness or in-process overdue days; missing delays are not zero.'],
            'chart_data':{'title':'Delayed or overdue home-delivery orders','labels':[r['location'] for r in table],'datasets':[{'label':'Orders','values':[r['delayed_or_overdue_orders'] for r in table]}],'interpretation':'Observed order-level delivery indicators at the source snapshot, not live courier status.'}}

    def competition(self,ctx,state,text):
        if state.get('sku_id') or state.get('filters'):
            # Benchmarks only have store/category grain; never silently apply variant/channel filters to estimates.
            return {'status':'unavailable','summary':'Competitor estimates are available at store/category/week level. Clear variant or channel filters to compare that population.','actions':[{'label':'Clear filters (type “clear filters”)','action':'sales'}]}
        with self.db.session() as s:
            clauses=filters(ctx,state,CompetitorSale)
            peers=s.execute(select(CompetitorSale.competitor,func.sum(CompetitorSale.units),func.sum(CompetitorSale.revenue_paise)).where(*clauses).group_by(CompetitorSale.competitor)).all()
            own=select(CompetitorSale.week,CompetitorSale.store_id,CompetitorSale.category,func.max(CompetitorSale.payload['our_units_sold'].as_integer()).label('units')).where(*clauses).group_by(CompetitorSale.week,CompetitorSale.store_id,CompetitorSale.category).subquery()
            ours=s.scalar(select(func.sum(own.c.units))) or 0
            observed_weeks=s.execute(select(func.min(CompetitorSale.week),func.max(CompetitorSale.week)).where(*clauses)).one()
            known=[n for n,_,_ in peers];matches=[n for n in known if key(n) in text]
            price_clauses=filters(ctx,state)+[Sale.payload['benchmark_competitor'].as_string().in_(matches or known)]
            net,quantity,peer_price=s.execute(select(func.sum(Sale.net_paise),func.sum(Sale.quantity),func.sum(Sale.payload['competitor_price_inr'].as_float()*Sale.quantity)).where(*price_clauses)).one()
        total=ours+sum(n for _,n,_ in peers)
        rows=[{'competitor':name,'estimated_units':n,'estimated_revenue_inr':str(Decimal(money)/100)} for name,n,money in peers if not matches or name in matches]
        finding='Weekly synthetic competitor estimates; these are not verified company results. Own units are counted once per store/category/week, not repeated for each competitor.'
        if quantity and peer_price:
            finding+=f' On matched transaction benchmarks, our quantity-weighted net unit price is INR {Decimal(net)/100/quantity:.2f}; competitor shelf price is INR {peer_price/quantity:.2f}.'
        return {'status':'success' if rows else 'no_data','summary':f"{len(rows)} tracked competitor labels in the selected store/category benchmark weeks. Estimates cover whole overlapping weeks, not just selected transaction dates.",'table':rows,
            'metrics':{'Our units in benchmark weeks':ours,'Our share of all tracked units (%)':round(ours/total*100,2) if total else None},'findings':[finding,f'Benchmark week starts: {observed_weeks[0]} to {observed_weeks[1]}.'],
            'chart_data':{'title':'Estimated competitor units','labels':[r['competitor'] for r in rows],'datasets':[{'label':'Estimated units','values':[r['estimated_units'] for r in rows]}],'interpretation':finding}}

    def forecast(self,ctx,state,text):
        match=re.search(r'(?:next|forecast)\s+(\d+)\s+days?',text);horizon=int(match.group(1)) if match else 7
        if not 1<=horizon<=90:raise ValueError('Forecast horizon must be 1-90 days')
        clauses=filters(ctx,state,period=False)+[Sale.day<=state['period']['end']]
        with self.db.session() as s:observed=s.execute(select(Sale.day,func.sum(Sale.quantity)).where(*clauses).group_by(Sale.day).order_by(Sale.day)).all()
        days=[date.fromisoformat(d) for d,_ in observed];values=[n for _,n in observed]
        if len(days)<14 or days[-1].isoformat()!=state['period']['end'] or any((b-a).days!=1 for a,b in zip(days,days[1:])):
            return {'status':'insufficient_data','summary':'Forecast needs at least 14 contiguous observed days ending on the selected date. Missing transaction days are not silently filled with zero.'}
        evaluated=backtest(days,values);winner=evaluated[0]
        rows=[{'date':(days[-1]+timedelta(days=i)).isoformat(),'forecast_units':round(max(0,predict(winner['model'],days,values,days[-1]+timedelta(days=i))),2)} for i in range(1,horizon+1)]
        return {'status':'success','summary':f"{horizon}-day observed-sales forecast using {winner['model']}; chronological one-step MAE {winner['mae']:.2f} units.",'table':rows,
            'metrics':{'History days':len(days),'MAE':round(winner['mae'],2),'RMSE':round(winner['rmse'],2)},'validation':evaluated,
            'findings':['Forecasts reflect recorded sales, not unconstrained demand. No inventory or causal employee attribution is inferred. Model-selection metrics are not independent holdout accuracy.'],
            'chart_data':{'time':True,'title':'Forecast units','labels':[r['date'] for r in rows],'datasets':[{'label':'Forecast units','values':[r['forecast_units'] for r in rows]}],'interpretation':'Chronologically selected baseline forecast of recorded units. Future values are predictions, not observations.'}}
