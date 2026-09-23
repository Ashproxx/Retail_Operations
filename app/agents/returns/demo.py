import asyncio
from app.agents.returns.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role
async def main():
    records=[dict(store_id='s',order_id='fixture-order',observed_on='2026-01-01',delivered_on='2026-01-01',purchased_units=1,paid_total='100',policy=dict(window_days=30,allowed_reasons=['defect'],receipt_required=True,allow_opened=True,source='fixture://policy'),source='fixture://order',fixture=True)]
    print((await Agent(records).run(QueryRequest(session_id='demo',message='{"store_id":"s","order_id":"fixture-order","as_of":"2026-01-10","reason":"defect","has_receipt":true}'),RequestContext(session_id='demo',principal_id='fixture',role=Role.SUPPORT_AGENT,store_ids=['s']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
