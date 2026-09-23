from concurrent.futures import ThreadPoolExecutor
from app.api.schemas import AuditEvent
from app.integration.orchestrator import aggregate
from tests.integration.conftest import headers


def chat(client,message,parameters=None,role='manager',session='s',**extra):
    return client.post('/api/chat',headers=headers(role),json={'message':message,'session_id':session,'parameters':parameters or {},**extra})

def test_authentication_cannot_be_claimed_by_payload(client):
    assert client.post('/api/chat',json={'message':'inventory','session_id':'s'}).status_code==401
    assert client.post('/api/chat',headers=headers(),json={'message':'inventory','session_id':'s','role':'ADMIN'}).status_code==422
    assert client.post('/api/chat',headers={'Authorization':'Bearer nope'},json={'message':'inventory','session_id':'s'}).status_code==401


def test_single_agent_followup_and_owner_isolation(client):
    first=chat(client,'Which products are below their reorder point in Bandra?').json()
    assert first['agents_used']==['router','inventory']
    assert first['data']['status']=='success' and first['data']['fixture']
    assert first['data']['results']['inventory']['data']['items'][0]['store_id']=='BANDRA'
    follow=chat(client,'What about Andheri?').json()
    assert follow['data']['status']=='success'
    item=follow['data']['results']['inventory']['data']['items'][0]
    assert item['store_id']=='ANDHERI'
    assert follow['data']['results']['inventory']['data']['parameters_used']['action']=='low_stock'
    isolated=chat(client,'What about Andheri?',role='other').json()
    assert isolated['data']['requires_human']


def test_multi_agent_forecast_and_inventory(client):
    result=chat(client,'Inventory is low but demand is increasing.',
                {'store_id':'BANDRA','sku_id':'SHIRT-1','as_of':'2026-09-22'}).json()
    assert result['data']['status']=='success'
    assert result['agents_used']==['router','inventory','demand-forecasting']
    assert len(result['data']['results']['demand-forecasting']['data']['forecast'])==7
    assert result['data']['results']['demand-forecasting']['data']['depends_on_results']==['inventory']


def test_missing_sku_unknown_store_unknown_intent(client):
    for text,params in [('Forecast demand in Bandra',{}),('low stock in Atlantis',{}),('weather',{})]:
        result=chat(client,text,params).json()
        assert result['data']['requires_human']
    assert chat(client,'inventory',{'nonsense':1}).json()['data']['requires_human']


def test_authorization_before_repository_data_access(client,monkeypatch):
    # No rows may be read for a forbidden action; a manager also cannot select an ungranted store.
    blocked=chat(client,'inventory',role='analyst').json()
    assert blocked['data']['results']['inventory']['data']['reason']=='access_denied'
    blocked=chat(client,'inventory',{'store_id':'BANDRA'},role='other').json()
    assert blocked['data']['results']['inventory']['data']['reason']=='access_denied'
    assert 'SHIRT-1' not in str(blocked)


def test_conflict_escalates_without_mutating_observed_prices(client):
    result=chat(client,'low stock and discount',{'store_id':'BANDRA','sku_id':'SHIRT-1','as_of':'2026-09-22',
        'discount_pct':10,'promotion_start':'2026-09-01','promotion_end':'2026-09-30'}).json()
    assert result['data']['conflicts']
    assert result['data']['requires_human'] and not result['data']['operational_write_performed']
    assert result['data']['results']['pricing-promotions']['data']['observed']['current_price']=='100'


def test_all_domain_registry_entries_and_endpoints(client):
    params={'store_id':'BANDRA','sku_id':'SHIRT-1','as_of':'2026-09-22'}
    cases={
        'inventory':params,'demand-forecasting':params,'analytics-reporting':{'start':'2026-09-01','end':'2026-09-22'},
        'pricing-promotions':params,'supply-chain':params,
        'order-fulfillment':{'store_id':'BANDRA','order_id':'O1','as_of':'2026-09-22T12:00:00Z'},
        'returns-refunds':{'store_id':'BANDRA','order_id':'O1','as_of':'2026-09-22','mode':'refund_status'},
        'customer-service':{'store_id':'BANDRA','question':'Customer service FAQ opening hours','as_of':'2026-09-22'},
    }
    for agent,parameters in cases.items():
        response=client.post('/api/query',headers=headers(),json={'agent':agent,'session_id':agent,'parameters':parameters})
        assert response.status_code==200,(agent,response.text)
        data=response.json()
        assert data['data']['status']=='success',(agent,data)
        assert agent in data['agents_used']
    assert client.get('/api/inventory/low-stock',headers=headers()).status_code==200
    assert client.get('/api/inventory/BANDRA',headers=headers()).status_code==200
    summary=client.get('/api/analytics/summary',headers=headers()).json()
    assert summary['data']['results']['analytics-reporting']['data']['summary']['units_sold']==105
    assert client.post('/api/forecast',headers=headers(),json={'message':'forecast','session_id':'f','parameters':params}).json()['data']['status']=='success'


def test_audit_feedback_and_provider_fallback(client,monkeypatch):
    from app.core.exceptions import ComponentUnavailableError
    async def unavailable(_):raise ComponentUnavailableError('private provider URL')
    monkeypatch.setattr(client.app.state.runtime.orchestrator.provider,'draft',unavailable)
    response=chat(client,'low stock',draft_with_llm=True).json()
    assert response['data']['llm_warning'] and response['data']['status']=='success'
    request_id=response['data']['request_id']
    feedback={'request_id':request_id,'session_id':'s','rating':1,'comment':'useful'}
    assert client.post('/api/feedback',headers=headers('manager'),json=feedback).status_code==200
    assert client.post('/api/feedback',headers=headers('other'),json=feedback).status_code==403
    assert client.get('/api/audit',headers=headers('manager')).status_code==403
    audit=client.get('/api/audit',headers=headers()).json()
    assert audit['anchor']['count']>=2
    assert all('message' not in row['event'] for row in audit['events'])
    assert 'private provider URL' not in str(response)


def test_agent_failure_and_reduced_scope_followup(client,monkeypatch):
    from app.agents.inventory.agent import Agent
    from app.security.policy import TokenAuthenticator,Grant
    import hashlib
    from tests.integration.conftest import TOKENS
    chat(client,'low stock in Bandra')
    client.app.state.runtime.auth=TokenAuthenticator([Grant(principal_id='manager',role='STORE_MANAGER',store_ids=['ANDHERI'],
        token_sha256=hashlib.sha256(TOKENS['manager'].encode()).hexdigest())])
    follow=chat(client,'What about Bandra?').json()
    assert follow['data']['requires_human']
    async def fail(*args):raise RuntimeError('secret agent payload')
    monkeypatch.setattr(Agent,'run',fail)
    response=chat(client,'inventory',{'store_id':'ANDHERI'}).json()
    assert response['data']['status']=='error' and 'secret agent payload' not in str(response)


def test_openapi_and_rag_missing_configuration(client):
    paths=client.get('/openapi.json').json()['paths']
    for path in ['/api/chat','/api/query','/api/forecast','/api/rag/ingest','/api/rag/query','/api/feedback','/api/audit']:
        assert path in paths
    response=client.post('/api/rag/query',headers=headers(),json={'session_id':'s','question':'opening hours','store_id':'BANDRA','domain':'support'})
    assert response.status_code==503


def test_representative_prompt_queries(client):
    params={'store_id':'BANDRA','sku_id':'SHIRT-1','as_of':'2026-09-22'}
    for message in [
        'Which products are currently below their reorder point?',
        'Which SKUs have the highest stockout risk?',
        'Show total units sold by store.',
        'Which products sold the most?',
        'Forecast demand for a selected SKU.',
        'Which Bandra products may require replenishment soon?',
        'Inventory is low but demand is increasing. What actions should be considered?',
    ]:
        result=chat(client,message,params).json()
        assert result['data']['status']=='success',(message,result)
    assert result['data']['recommended_actions'][0]['advisory_only']
