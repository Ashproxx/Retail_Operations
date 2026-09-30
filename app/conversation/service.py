"""Progressive clarification and bounded evidence-led orchestration."""
import asyncio
import json
import re
from time import perf_counter
from datetime import datetime
from app.api.schemas import AuditEvent
from app.conversation.contracts import Context
from app.conversation.catalog import Catalog
from app.conversation.taxonomy import key, mentioned_category, mentioned_categories
from app.conversation import dates, analytics, charts
from app.conversation.forecast import forecast
from app.conversation.competition import compare
from app.security.policy import AccessDenied
from app.core.exceptions import ComponentUnavailableError
from app.integration.contracts import DirectQuery

INTENTS=['sales','inventory','forecast','diagnose','recommendations','competition','support','pricing','orders','supply','returns']
CHART_WORDS={'stacked bar':'stacked_bar','grouped bar':'grouped_bar','horizontal bar':'horizontal_bar','multi-line':'multi_line',
             'doughnut':'doughnut','donut':'doughnut','heatmap':'heatmap','scatter':'scatter','pie':'pie','area':'area','line':'line','bar':'bar'}


def intent_of(message):
    text=key(message)
    if re.search(r'\b(refund|return)\b',text):return 'returns'
    if re.search(r'\b(order|delivery|shipping)\b',text):return 'orders'
    if re.search(r'\b(suppliers?|supply chain|vendors?|lead time)\b',text):return 'supply'
    if re.search(r'\b(policy|faq|opening hours|customer service|sop)\b',text):return 'support'
    if re.search(r'\b(compete|competes|competition|competitors?|similar products?|substitutes?)\b',text):return 'competition'
    if re.search(r'\b(forecast|predict|season|seasonality|next \d+ days)\b',text):return 'forecast'
    if re.search(r'\b(should|recommend|suggest|actions?|improve|do about)\b',text):return 'recommendations'
    if re.search(r'\b(why|poorly|poor|worst|low sales|not selling|declin|underperform)',text):return 'diagnose'
    if re.search(r'\b(stock|inventory|reorder|availability)\b',text):return 'inventory'
    if re.search(r'\b(price|pricing|discount|promotion)\b',text):return 'pricing'
    if re.search(r'\b(sales|sold|selling|revenue|units|performance|perform|doing|did we|show|shirts|shorts|pants|clothing)\b',text):return 'sales'
    return None


def options(values):return [{'label':str(v),'value':str(v)} for v in values]


def public_context(ctx):
    return ctx.model_dump(exclude={'store_id','sku_id','pending','previous_intent','order_id','original_question','business_details'})


class ConversationService:
    def __init__(self,runtime,clock=None):
        self.runtime=runtime;self.clock=clock;self.lock=asyncio.Lock()

    async def run(self,turn,principal):
        async with self.lock:
            started=perf_counter();response=None
            try:
                response=await self._run(turn,principal)
                if not response.pop('legacy_receipt',False):self.runtime.repository.receipt(principal)
                response['request_id']=str(principal.request_id)
                return response
            finally:
                self.runtime.audit.append(AuditEvent(request_id=principal.request_id,session_id=principal.session_id,
                    user_role=principal.role,agents_called=(response or {}).get('agents',[]),
                    tools_called=['conversation.authorized_tools']+(['rag.retrieve_verified'] if (response or {}).get('policy_evidence') else []),
                    documents_retrieved=[h['chunk']['document_id'] for h in (response or {}).get('policy_evidence',{}).get('sources',[])],
                    rag_iterations=(response or {}).get('policy_evidence',{}).get('iterations',0),confidence=0,
                    latency_ms=(perf_counter()-started)*1000,final_status=(response or {}).get('status','error')))

    async def _run(self,turn,principal):
        state_owner=principal.model_copy(update={'session_id':'conversation:'+principal.session_id})
        saved=self.runtime.repository.memory(state_owner)
        ctx=Context.model_validate(saved['context']) if saved and saved.get('version')==2 else Context()
        if turn.action=='reset':ctx=Context()
        message=turn.message.strip();text=key(message)
        selected_chart = turn.action=='select' and ctx.pending=='chart'
        if turn.action=='select' and ctx.pending=='intent' and turn.value in INTENTS:
            ctx.intent=turn.value;ctx.pending=None
        catalog=Catalog(self.runtime,principal)
        intent=intent_of(message)
        if turn.action in INTENTS:intent=turn.action
        if re.search(r'\b(it|that|why|what about|graph|chart|pie|line|bar|area)\b',text) and ctx.intent and not intent:
            intent=ctx.intent
        combined=[intent_of(part) for part in re.split(r'\band\b|\bplus\b|\balso\b|;',message,flags=re.I)]
        combined=list(dict.fromkeys(i for i in combined if i in ['sales','inventory','forecast','pricing','competition','recommendations','diagnose']))
        if len(combined)>1:
            ctx.requested_intents=combined;intent='recommendations' if 'recommendations' in combined or 'diagnose' in combined else 'sales'
        elif intent and ctx.pending is None:ctx.requested_intents=[]
        if intent:
            if intent!=ctx.intent:ctx.business_details={};ctx.order_id=None
            ctx.previous_intent=ctx.intent
            ctx.intent=intent
            if message:ctx.original_question=message
        if not ctx.intent:
            # Optional local language model only classifies an allowlisted intent; no facts or authority.
            if message and self.runtime.provider is not None:
                try:
                    raw=await self.runtime.provider.draft('Classify the following retail request. Return ONLY JSON with intent and confidence. Allowed intents: '+','.join(INTENTS)+'. Unknown requests use null. Request: '+message[:1500])
                    guess=json.loads(raw)
                    if isinstance(guess,dict) and guess.get('intent') in INTENTS and isinstance(guess.get('confidence'),(int,float)) and guess['confidence']>=.85:ctx.intent=guess['intent']
                except (ValueError,TypeError,ComponentUnavailableError):pass
            if not ctx.intent:
                ctx.pending='intent'
                return self.clarify(ctx,state_owner,'What would you like to explore?','intent',options(['sales','inventory','forecast','competition','recommendations']))
        action='inventory.read' if ctx.intent=='inventory' else 'forecast.read' if ctx.intent=='forecast' else 'analytics.read'
        # Support/order policies keep the original scoped agent tools; catalog disclosure is not required.
        if ctx.intent in ['support','orders','returns','supply','pricing']:
            return await self.legacy(turn,ctx,state_owner,principal)
        rows=catalog.observations(action=action)
        if not rows:
            ctx.pending=None
            return self.save(ctx,state_owner,{'status':'no_data','summary':'No authorized retail observations are loaded for this operation. Import your dataset or start the explicitly synthetic showcase.','actions':[]})
        stores={r['store_id']:r['store_location'] for r in rows}
        # Reauthorization also invalidates selections from a formerly permitted scope.
        if ctx.store_id and ctx.store_id not in stores:
            ctx.store_id=ctx.location=ctx.sku_id=ctx.product=None
        available=(min(r['date'] for r in rows),max(r['date'] for r in rows))
        period=dates.resolve(message,now=self.clock() if self.clock else None,timezone=ctx.timezone,available=available) if message else None
        if period:
            if re.search(r'compare|compared',text) and ctx.period:ctx.comparison_period=period
            else:ctx.period=period;ctx.comparison_period=None
        if re.search(r'\bunits\b',text):ctx.metric='units'
        elif re.search(r'\brevenue|price|sales\b',text):ctx.metric='revenue'
        horizon=re.search(r'(?:next|forecast)\s+(\d+)\s+days?',text)
        if horizon:
            number=int(horizon.group(1))
            if not 1<=number<=90:return self.clarify(ctx,state_owner,'Choose a forecast horizon from 1 to 90 days.','horizon',options(['7','14','30']))
            ctx.horizon=number
        if turn.action=='locations':ctx.store_id=ctx.location=None;ctx.pending='location'
        if turn.action=='period':ctx.period=None;ctx.pending='period'
        if turn.action=='products':ctx.sku_id=ctx.product=None;ctx.pending='product'
        if turn.action=='compare':ctx.store_id=None;ctx.location='All authorized locations';ctx.group_by='store_category'
        matches=[(sid,name) for sid,name in stores.items() if re.search(r'(?<!\w)'+re.escape(key(name))+r'(?!\w)',text)]
        if len(matches)==1:ctx.store_id,ctx.location=matches[0]
        elif len(matches)>1 or re.search(r'compare (?:stores|locations)|all (?:stores|locations)',text):
            ctx.store_id=None;ctx.location='All authorized locations';ctx.group_by='store_category'
        local=[r for r in rows if not ctx.store_id or r['store_id']==ctx.store_id]
        products=catalog.products(local)
        cats=catalog.discover('normalized_category',local)
        mentioned=mentioned_categories(message)
        if mentioned:
            missing=[c for c in mentioned if c not in cats]
            if missing:return self.save(ctx,state_owner,{'status':'no_data','summary':'No authorized observations for '+', '.join(missing)+'. Available categories: '+', '.join(cats)+'.','actions':[{'label':'Choose a product','action':'products'}]})
            ctx.categories=mentioned if len(mentioned)>1 else []
            ctx.category=mentioned[0] if len(mentioned)==1 else None
            ctx.sku_id=ctx.product=None
        if re.search(r'\ball products\b|\ball categories\b',text):
            ctx.category=ctx.sku_id=ctx.product=ctx.gender=ctx.size=ctx.color=None;ctx.categories=[]
        product_matches=[p for p in products if len(p['label'])>2 and key(p['label']) in text]
        if len(product_matches)==1:ctx.sku_id=product_matches[0]['value'];ctx.product=product_matches[0]['label'];ctx.category=None
        for dimension in ['gender','size','color']:
            matched=[v for v in catalog.discover(dimension,local) if re.search(r'(?<!\w)'+re.escape(key(v))+r'(?!\w)',text)]
            if len(matched)==1:setattr(ctx,dimension,matched[0])
        if turn.action=='select' and not (turn.value in INTENTS and ctx.pending is None):
            value=turn.value or ''
            if ctx.pending=='intent' and value in INTENTS:ctx.intent=value
            elif ctx.pending=='location' and value in stores:ctx.store_id=value;ctx.location=stores[value]
            elif ctx.pending=='period':
                ctx.period=dates.resolve(value,now=self.clock() if self.clock else None,timezone=ctx.timezone,available=available)
                if not ctx.period:raise ValueError('Choose a listed period or provide YYYY-MM-DD to YYYY-MM-DD.')
            elif ctx.pending=='product' and any(p['value']==value for p in products):
                p=next(p for p in products if p['value']==value);ctx.sku_id=p['value'];ctx.product=p['label'];ctx.category=None;ctx.categories=[]
            elif ctx.pending=='chart':ctx.chart_type=value
            elif ctx.pending=='horizon' and value in ['7','14','30']:ctx.horizon=int(value)
            else:return self.clarify(ctx,state_owner,'That option is no longer available. Please choose again.','location',[{'label':n,'value':s} for s,n in stores.items()])
            ctx.pending=None
        elif ctx.pending=='intent' and text in INTENTS:ctx.intent=text;ctx.pending=None
        elif ctx.pending=='product' and not ctx.sku_id:
            exact=[p for p in products if key(p['label'])==text]
            if len(exact)==1:ctx.sku_id=exact[0]['value'];ctx.product=exact[0]['label'];ctx.category=None;ctx.pending=None
        if not ctx.location:
            return self.clarify(ctx,state_owner,'Which location would you like to analyse?','location',[{'label':n,'value':s} for s,n in stores.items()])
        if ctx.store_id and ctx.store_id not in stores:raise AccessDenied('Store scope changed')
        if not ctx.period:
            return self.clarify(ctx,state_owner,'Which period would you like to analyse?','period',options(dates.PERIODS))
        filtered=analytics.select_rows(rows,ctx)
        if ctx.previous_intent=='competition' and ctx.intent=='diagnose' and re.search(r'\b(that one|this one)\b',text):
            ctx.sku_id=ctx.product=ctx.category=None;ctx.categories=[];ctx.pending='product'
        if ctx.pending=='product' or ctx.intent=='competition' and not ctx.sku_id:
            scoped_products=catalog.products(analytics.select_rows(rows,ctx.model_copy(update={'sku_id':None})))
            return self.clarify(ctx,state_owner,'Which product would you like to investigate?','product',scoped_products)
        if ctx.sku_id and not any(r['sku_id']==ctx.sku_id for r in local):
            ctx.sku_id=ctx.product=None
            return self.clarify(ctx,state_owner,'That product is unavailable in this location. Which product?','product',catalog.products(local))
        if not filtered:
            return self.save(ctx,state_owner,{'status':'no_data','summary':f"No observations match {ctx.period['label']} at {ctx.location}. Available data runs from {available[0]} to {available[1]}. Missing records are not zero sales.",
                'actions':[{'label':'Change period','action':'period'},{'label':'Change location','action':'locations'}],
                'available_dates':available})
        if ctx.intent=='inventory':
            current=analytics.latest(filtered)
            result={'status':'success','summary':f"{len(current)} observed product/location snapshots; {sum(r.get('closing_stock') or 0 for r in current)} units of closing stock.",
                    'inventory':[{'product':r['product_label'],'location':r['store_location'],'stock':r.get('closing_stock'),
                                  'reorder_point':r.get('reorder_point'),'observed':r['date']} for r in current],
                    'agents':['inventory'],'warnings':['Closing stock is an observed snapshot, not a live reservation-adjusted availability promise.']}
        elif ctx.intent=='forecast':
            result=forecast(rows,ctx);result['agents']=['demand-forecasting']
        elif ctx.intent=='competition':
            result=compare(rows,ctx,catalog);result['agents']=['competition-intelligence']
        else:
            result=analytics.analyze(rows,ctx);result['agents']=['analytics']
            if ctx.intent in ['diagnose','recommendations']:
                result['agents']+=['inventory-diagnostics','pricing-context','demand-forecasting','competition-intelligence','market-calendar']
                result['demand']=forecast(rows,ctx)
                if not ctx.sku_id and result['diagnostics']:
                    chosen=result['diagnostics'][0];ctx.sku_id=chosen['sku_id'];ctx.product=chosen['label']
                result['competition']=compare(rows,ctx,catalog) if ctx.sku_id else {'status':'insufficient_data'}
                result['pricing_context']={'observed_average_price_inr':result['key_numbers'].get('average_selling_price_inr'),
                    'limitation':'Costs, margins and approved discount policy may be missing; no discount is authorized.'}
                try:
                    policy=self.runtime.rag.query('marketing promotion pricing policy',principal,ctx.store_id,'pricing') if ctx.store_id else None
                    if policy:result['policy_evidence']=policy.model_dump(mode='json')
                except ComponentUnavailableError:result['rag_status']='Local policy RAG is not configured; no external fallback or policy claim.'
                except AccessDenied:result['rag_status']='Policy evidence is outside this role scope.'
                if result['diagnostics']:result['findings'].append(result['diagnostics'][0]['explanation'])
        if ctx.intent in ['diagnose','recommendations'] or len(ctx.requested_intents)>1:
            if 'forecast' in ctx.requested_intents and 'demand' not in result:
                try:result['demand']=forecast(catalog.observations(action='forecast.read'),ctx);result['agents'].append('demand-forecasting')
                except AccessDenied:result['demand']={'status':'denied','summary':'Forecasting is outside this role scope.'}
            if 'inventory' in ctx.requested_intents:
                try:
                    snapshots=analytics.latest(analytics.select_rows(catalog.observations(action='inventory.read'),ctx))
                    result['inventory']=[{'product':r['product_label'],'location':r['store_location'],'stock':r.get('closing_stock'),'reorder_point':r.get('reorder_point'),'observed':r['date']} for r in snapshots]
                    result['agents'].append('inventory')
                except AccessDenied:result.setdefault('warnings',[]).append('Inventory is outside this role scope.')
            if ctx.store_id and ctx.sku_id:
                executed=await self.runtime.orchestrator.execute({'context':principal,'targets':['pricing-promotions'],'message':'Read-only pricing evidence',
                    'parameters':{'store_id':ctx.store_id,'sku_id':ctx.sku_id,'as_of':ctx.period['end']}})
                result['pricing_evidence']=executed['results'][0]['result'].model_dump(mode='json')
                result['agents'].append('pricing-promotions')
            elif 'pricing' in ctx.requested_intents:
                result['pricing_context']={'status':'needs_product','limitation':'Select a product to inspect its authorized pricing observations. No cost or margin was inferred.'}
        wants_chart=selected_chart or turn.action in ['visualize','chart'] or bool(re.search(r'graph|chart|visuali[sz]|\bpie\b|\bdoughnut\b',text)) or ctx.pending=='chart'
        for phrase,kind in CHART_WORDS.items():
            if re.search(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)',text):ctx.chart_type=kind;wants_chart=True;break
        if turn.action=='chart':ctx.chart_type=turn.value;wants_chart=True
        if re.search(r'over time|daily|trend line',text):ctx.group_by='date'
        if re.search(r'price.*units|scatter',text):ctx.group_by='price_units'
        if re.search(r'by (?:store|location)',text):ctx.group_by='store'
        if ctx.group_by=='store_category' and len({r['store_id'] for r in filtered})==1:ctx.group_by='category'
        if wants_chart and ctx.intent in ['sales','diagnose','recommendations']:
            allowed=charts.compatible(ctx.group_by,filtered)
            if ctx.chart_type not in allowed:
                return self.clarify(ctx,state_owner,'How would you like to visualize these results?','chart',options(allowed),result)
            result['visualization']=charts.specification(rows,ctx)
        result.setdefault('actions',[{'label':label,'action':action} for label,action in [('View graph','visualize'),('Change period','period'),('Compare locations','compare'),('Products','products'),('Low sales','diagnose'),('Forecast','forecast'),('Competition','competition'),('Suggest actions','recommendations'),('Inventory','inventory')]])
        if ctx.intent=='forecast':result['actions']=[{'label':'Change period','action':'period'},{'label':'Sales analysis','action':'sales'},{'label':'Select product','action':'products'}]
        if ctx.sku_id:result['product360']=catalog.product360(analytics.select_rows(rows,ctx.model_copy(update={'sku_id':None,'category':None,'categories':[],'gender':None,'color':None,'size':None})),ctx.sku_id)
        result['fixture']=any(r.get('fixture') for r in filtered)
        result.setdefault('sources',sorted({r['source'] for r in filtered}))
        ctx.pending=None
        return self.save(ctx,state_owner,result)

    def save(self,ctx,owner,result):
        self.runtime.repository.remember(owner,{'version':2,'context':ctx.model_dump()})
        return {**result,'context':public_context(ctx),'operational_write_performed':False}

    def clarify(self,ctx,owner,question,field,choices,result=None):
        ctx.pending=field
        return self.save(ctx,owner,{**(result or {}),'status':'needs_clarification','summary':question,
            'clarification':{'field':field,'question':question,'options':choices[:1000]},'agents':['router','clarification'],
            'actions':[],'requires_human':False})

    async def legacy(self,turn,ctx,owner,principal):
        """Read-only domain adapters with progressive, scoped business choices."""
        agent={'support':'customer-service','orders':'order-fulfillment','returns':'returns-refunds',
               'supply':'supply-chain','pricing':'pricing-promotions'}[ctx.intent]
        records=self.runtime.repository.records(agent,principal)
        known=self.runtime.repository.stores(principal)
        stores={r['store_id']:known.get(r['store_id'],'Location '+str(i+1)) for i,r in enumerate(records)}
        if not stores:
            return self.save(ctx,owner,{'status':'no_data','summary':'No authorized '+ctx.intent+' records are loaded. No business facts were inferred.','actions':[],'agents':['router']})
        matches=[(s,n) for s,n in stores.items() if re.search(r'(?<!\w)'+re.escape(key(n))+r'(?!\w)',key(turn.message))]
        if len(matches)==1:
            if ctx.store_id!=matches[0][0]:ctx.order_id=ctx.sku_id=None;ctx.business_details={}
            ctx.store_id,ctx.location=matches[0]
        if ctx.store_id not in stores:ctx.store_id=ctx.location=None
        if turn.action=='select' and ctx.pending=='location' and turn.value in stores:
            ctx.store_id=turn.value;ctx.location=stores[turn.value];ctx.pending=None
        if not ctx.store_id:return self.clarify(ctx,owner,'Which location?','location',[{'label':n,'value':s} for s,n in stores.items()])
        records=[r for r in records if r['store_id']==ctx.store_id]
        params={'store_id':ctx.store_id,'as_of':dates.today().isoformat()}
        if ctx.intent=='support':params['question']=ctx.original_question or turn.message or 'Customer service FAQ'
        if ctx.intent in ['pricing','supply']:
            products={r['sku_id']:None for r in records}
            # Human labels come from authorized catalog data where that role permits it.
            try:
                action='forecast.read' if ctx.intent=='pricing' else 'inventory.read'
                catalog=Catalog(self.runtime,principal)
                names={p['value']:p['label'] for p in catalog.products(catalog.observations(ctx.store_id,action=action))}
            except AccessDenied:names={}
            choices=[{'value':sku,'label':names.get(sku,'Product '+str(i+1))} for i,sku in enumerate(products)]
            if turn.action=='select' and ctx.pending=='business_product' and turn.value in products:
                ctx.sku_id=turn.value;ctx.pending=None
            matches=[p for p in choices if key(p['label']) in key(turn.message)]
            if len(matches)==1:ctx.sku_id=matches[0]['value']
            if ctx.sku_id not in products:return self.clarify(ctx,owner,'Which product?','business_product',choices)
            params['sku_id']=ctx.sku_id
            params['mode']='recommend' if ctx.intent=='pricing' else 'compare'
        if ctx.intent in ['orders','returns']:
            orders={r['order_id']:r for r in sorted(records,key=lambda r:r.get('updated_at',r.get('observed_on','')))}
            choices=[{'value':oid,'label':f"Purchase {i+1} · {(r.get('placed_at') or r.get('delivered_on') or r.get('observed_on',''))[:10]} · {r.get('state',r.get('refund_status') or 'return record')}"} for i,(oid,r) in enumerate(orders.items())]
            if turn.action=='select' and ctx.pending=='order' and turn.value in orders:
                ctx.order_id=turn.value;ctx.pending=None;ctx.business_details={}
            if ctx.order_id not in orders:return self.clarify(ctx,owner,'Which purchase would you like to check?','order',choices)
            params['order_id']=ctx.order_id
            if ctx.intent=='orders':params.update(as_of=datetime.now().astimezone().isoformat(),mode='status')
            elif 'refund' in key(ctx.original_question):params['mode']='refund_status'
            else:
                questions=[('reason','What is the reason for the return?',options(['defect','wrong_item','change_of_mind','other'])),
                           ('has_receipt','Do you have the receipt?',options(['Yes','No'])),
                           ('opened','Has the item been opened?',options(['Yes','No'])),
                           ('units_requested','How many units do you want to return?',options([str(i) for i in range(1,min(orders[ctx.order_id]['purchased_units']-orders[ctx.order_id]['previously_returned_units'],100)+1)]))]
                if turn.action=='select' and ctx.pending in {q[0] for q in questions}:
                    valid=next(q[2] for q in questions if q[0]==ctx.pending)
                    if turn.value in {v['value'] for v in valid}:
                        value=turn.value
                        ctx.business_details[ctx.pending]=(value=='Yes') if ctx.pending in ['has_receipt','opened'] else int(value) if ctx.pending=='units_requested' else value
                        ctx.pending=None
                for field,question,choices in questions:
                    if field not in ctx.business_details:
                        if not choices:return self.save(ctx,owner,{'status':'no_data','summary':'No remaining purchased units are recorded for return.','actions':[]})
                        return self.clarify(ctx,owner,question,field,choices)
                params.update(mode='eligibility',**ctx.business_details)
        response=await self.runtime.orchestrator.run(DirectQuery(session_id=principal.session_id,agent=agent,parameters=params),principal)
        return self.save(ctx,owner,{'status':response.data['status'],'summary':response.answer,
            'sources':[s.model_dump() for s in response.sources],'evidence':response.data['results'],
            'agents':response.agents_used,'legacy_receipt':True,'fixture':any(r.get('fixture') for r in records),
            'actions':[{'label':'Sales analysis','action':'sales'}]})
