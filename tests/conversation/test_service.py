import hashlib
from datetime import datetime,timezone,timedelta,date
import pytest
from app.api.schemas import RequestContext
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.services.database_service import Database
from app.conversation.catalog import import_observations
from app.conversation.contracts import Turn
from app.conversation.service import ConversationService


def seeded(tmp_path):
    db=Database('sqlite:///'+str(tmp_path/'db'))
    rt=Runtime(db,RuntimeSettings(_env_file=None,state_dir=tmp_path/'state',llm_provider='deterministic'),grants=[])
    rows=[]
    for store,name in [('A','Bandra'),('B','Andheri')]:
        for sku,category,style in [('P1','shirt','Oxford Shirt'),('P2','shorts','Cotton Shorts'),('P3','formal shirt','Linen Shirt')]:
            for i in range(60):
                rows.append(dict(date=(date(2026,7,31)+timedelta(days=i)).isoformat(),store_id=store,store_location=name,
                    sku_id=sku,category=category,style_name=style,units_sold=2 if sku=='P2' else 10,unit_price_inr='100',closing_stock=0 if sku=='P2' else 50,reorder_point=10))
    import_observations(db,rows,source='test-fixture',fixture=True)
    return db,rt


def test_progressive_slots_followups_and_chart_choice(tmp_path):
    import asyncio
    db,rt=seeded(tmp_path);svc=ConversationService(rt,clock=lambda:datetime(2026,9,28,10,tzinfo=timezone.utc))
    def ask(message='',action=None,value=None,session='s',principal='one'):
        ctx=RequestContext(session_id=session,principal_id=principal,role='STORE_MANAGER',store_ids=['A','B'])
        return asyncio.run(svc.run(Turn(message=message,session_id=session,action=action,value=value),ctx))
    r=ask("I want today's sales")
    assert r['clarification']['field']=='location'
    assert [x['label'] for x in r['clarification']['options']]==['Bandra','Andheri']
    r=ask('Bandra');assert r['status']=='success';assert r['context']['period']['label']=='Today'
    assert r['key_numbers']['units']=='22'
    r=ask('What about last week?');assert r['context']['location']=='Bandra';assert r['context']['period']['start']=='2026-09-21'
    r=ask('Show me a graph');assert r['clarification']['field']=='chart'
    r=ask(action='select',value='pie');assert r['visualization']['type']=='pie'
    assert r['visualization']['interpretation']
    r=ask('Why are shorts not selling?');assert r['diagnostics'][0]['status']=='STOCK_CONSTRAINED'
    r=ask('What should we do about it?');assert r['recommendations'];assert not r['operational_write_performed']
    r=ask('Who competes with it?');assert 'not configured' in r['external_status']
    other=ask('Bandra',session='new');assert other['status']=='needs_clarification'
    db.close()


def test_options_reauthorize_and_context_is_principal_scoped(tmp_path):
    import asyncio
    db,rt=seeded(tmp_path);svc=ConversationService(rt)
    ctx=RequestContext(session_id='same',principal_id='first',role='STORE_MANAGER',store_ids=['A'])
    r=asyncio.run(svc.run(Turn(message='Show sales',session_id='same'),ctx))
    assert [x['label'] for x in r['clarification']['options']]==['Bandra']
    ctx2=RequestContext(session_id='same',principal_id='second',role='STORE_MANAGER',store_ids=['B'])
    r=asyncio.run(svc.run(Turn(message='Why?',session_id='same'),ctx2))
    assert r['context']['location'] is None
    assert [x['label'] for x in r['clarification']['options']]==['Andheri']
    db.close()
