import asyncio,hashlib
from app.agents.support.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role
async def main():
    text='Fixture refund policy requires receipt within thirty days.'
    records=[dict(store_id='s',document_id='fixture-policy',version='1',valid_from='2026-01-01',approved=True,text=text,expected_sha256=hashlib.sha256(text.encode()).hexdigest(),source='fixture://policy',fixture=True)]
    print((await Agent(records).run(QueryRequest(session_id='demo',message='{"store_id":"s","question":"refund receipt","as_of":"2026-01-02"}'),RequestContext(session_id='demo',principal_id='fixture',role=Role.SUPPORT_AGENT,store_ids=['s']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
