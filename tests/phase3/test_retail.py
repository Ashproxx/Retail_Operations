from types import SimpleNamespace
from uuid import uuid4
from app.api.schemas import RequestContext
from app.integration.repository import Repository
from app.security.audit import AuditChain
from app.services.database_service import Database
from app.enterprise import imports
from app.enterprise.retail import RetailService
from app.enterprise.contracts import WorkspaceTurn
from tests.phase3.test_imports import small_sales


def test_sql_conversation_latest_chart_and_inventory_boundary(tmp_path,monkeypatch):
    path=tmp_path/'sales.xlsx';path.write_bytes(b'fixture')
    monkeypatch.setattr(imports,'sheets',lambda *a:small_sales())
    db=Database('sqlite:///'+str(tmp_path/'db'));imports.import_sales(db,path)
    rt=SimpleNamespace(repository=Repository(db),audit=AuditChain(tmp_path/'audit'))
    svc=RetailService(rt)
    def ask(message='',**kw):
        ctx=RequestContext(principal_id='m',session_id='test',role='STORE_MANAGER',store_ids=['S1'])
        return svc.run(WorkspaceTurn(session_id='test',message=message,**kw),ctx)
    assert ask('How were sales?')['choices'][0]['label']=='Test City'
    assert ask(action='select',value='S1')['status']=='needs_clarification'
    result=ask(action='select',value='latest')
    assert result['metrics']['Net sales (INR)']=='1199'
    result=ask('Show 2030-01-01 sales')
    assert result['status']=='no_data' and '2026-09-29' in result['summary']
    result=ask(action='latest');assert result['metrics']['Orders']==1
    assert ask('Show pie chart')['visualization']['datasets'][0]['values']==[1199.0]
    assert ask('current stock')['status']=='unavailable'
    assert ask('What is an employee salary?')['workspace']=='/employees'
    result=ask('competitor estimates');assert result['table'][0]['estimated_units']==5
    assert result['metrics']['Our units in benchmark weeks']==1
    db.close()


def test_question_specific_rankings_metrics_ties_and_followups(tmp_path,monkeypatch):
    from copy import deepcopy
    data=small_sales();base=data['Sales_Transactions'][0]
    for i,(name,quantity,amount) in enumerate([('Linen',3,900),('Denim',1,1100),('Silk',2,900)],2):
        row=deepcopy(base);row.update(txn_id='T'+str(i),order_id='O'+str(i),sku_id='P'+str(i),style_name=name,quantity=quantity,unit_price_inr=amount/quantity,discount_pct=0,net_amount_inr=amount)
        data['Sales_Transactions'].append(row)
    path=tmp_path/'sales.xlsx';path.write_bytes(b'ranking-fixture')
    monkeypatch.setattr(imports,'sheets',lambda *a:data)
    db=Database('sqlite:///'+str(tmp_path/'db'));imports.import_sales(db,path)
    svc=RetailService(SimpleNamespace(repository=Repository(db),audit=AuditChain(tmp_path/'audit')))
    ctx=RequestContext(principal_id='m',session_id='ranking',role='STORE_MANAGER',store_ids=['S1'])
    def ask(message='',**kw):return svc.run(WorkspaceTurn(session_id='ranking',message=message,**kw),ctx)
    ask('Show latest sales in Test City')
    low=ask('which product had the lowest sale')
    assert {r['group'] for r in low['table']}=={'Linen','Silk'}
    assert low['context']['group']=='product' and low['context']['rank']=='lowest'
    assert 'ties' in low['summary'] and low['metrics']['Compared product groups']==4
    units=ask('by units')
    assert {r['group'] for r in units['table']}=={'Oxford','Denim'}
    highest=ask('and the highest?')
    assert highest['table'][0]['group']=='Linen' and '3 units sold' in highest['summary']
    assert highest['context']['location']=='Test City' and highest['context']['period']['start']=='2026-09-29'
    assert 'do not establish why' in ask('Why?')['summary']
    chart=ask('show a bar chart')['visualization']
    assert chart['labels']==['Linen'] and chart['datasets'][0]['values']==[3]
    product=ask('Tell me about that product')
    assert len(product['table'])==1 and product['table'][0]['group']=='Linen'
    assert product['metrics']['Units']==3
    top=ask('top 2 products by revenue')
    assert [r['group'] for r in top['table']]==['Oxford','Denim']
    assert ask('and categories instead?')['context']['group']=='category'
    assert ask('by product')['context']['rank']=='highest'
    assert ask('write a birthday poem')['status']=='needs_clarification'
    assert 'rank' not in ask('show all sales')['context']
    delivery=ask('Which store has highest delivery delays?')
    assert delivery['context']['intent']=='delivery' and 'home-delivery' in delivery['summary']
    assert ask('Which product sold the least?')['context']['metric']=='units'
    ask('Compare stores')
    comparison=ask(action='chart',value='grouped_bar')['visualization']
    assert sum(sum(d['values']) for d in comparison['datasets'])==7
    db.close()
