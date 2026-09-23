import hashlib,pytest
from app.agents.support.domain import Policy,Query,evaluate,triage

def r(text='Refund requires receipt within thirty days.',**kw):return Policy(**dict(dict(store_id='s',document_id='p',version='1',valid_from='2026-01-01',approved=True,text=text,expected_sha256=hashlib.sha256(text.encode()).hexdigest(),source='fixture://policy',fixture=True),**kw))
def q(**kw):return Query(**dict(dict(store_id='s',question='refund receipt',as_of='2026-01-02'),**kw))

def test_grounded_excerpt_and_sources():
    result=evaluate([r()],q())
    assert result['status']=='success'
    assert result['sources'][0]['source']=='fixture://policy'
    assert result['answer'].endswith(r().text)

@pytest.mark.parametrize('rows',[[],[r(approved=False)],[r(valid_until='2026-01-01')],[r(store_id='other')],[r('Shipping takes three days.')]])
def test_no_fabricated_policy(rows):
    result=evaluate(rows,q())
    assert result['status']=='insufficient_evidence' and result['requires_human']

def test_tamper_and_conflicting_evidence():
    result=evaluate([r(expected_sha256='0'*64)],q())
    assert result['integrity_rejections']==1 and not result['sources']
    result=evaluate([r(),r('Refund requires receipt within seven days.',document_id='p2')],q())
    assert result['reason']=='conflicting_evidence'

def test_sentiment_negation_and_category():
    assert triage('I am not angry about delivery')['sentiment']=='neutral'
    assert triage('I am not happy about refund')['priority']=='human_review'
    assert triage('Terrible wrong item and delivery')['categories']==['returns','orders']

def test_duplicate_rejected():
    with pytest.raises(ValueError):evaluate([r(),r()],q())

def test_adapter_evidence_and_scope():
    import asyncio
    from app.agents.support.agent import Agent
    from app.api.schemas import QueryRequest,RequestContext,Role
    context=RequestContext(session_id='t',principal_id='u',role=Role.SUPPORT_AGENT,store_ids=['s'])
    result=asyncio.run(Agent([r()]).run(QueryRequest(session_id='t',message=q().model_dump_json()),context))
    assert result.evidence[0].document_id=='p'
    result=asyncio.run(Agent([r()]).run(QueryRequest(session_id='t',message=q(store_id='other').model_dump_json()),context))
    assert result.status=='escalated'
