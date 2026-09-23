import asyncio
from app.agents.orders.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role
async def main():
    agent=Agent([dict(store_id='s',order_id='fixture-order',sku_id='shirt',quantity=5,state='created',placed_at='2026-01-01T00:00:00Z',updated_at='2026-01-01T00:00:00Z',promised_at='2026-01-03T00:00:00Z',source='fixture://order',fixture=True)])
    print((await agent.run(QueryRequest(session_id='demo',message='{"store_id":"s","order_id":"fixture-order","as_of":"2026-01-04T00:00:00Z"}'),RequestContext(session_id='demo',principal_id='fixture',role=Role.SUPPORT_AGENT,store_ids=['s']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
