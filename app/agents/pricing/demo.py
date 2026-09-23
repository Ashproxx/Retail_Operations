import asyncio
from app.agents.pricing.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role
async def main():
    agent=Agent([dict(store_id='s',sku_id='shirt',observed_on='2026-01-01',current_price='100',unit_cost='50',stock_units=20,promotion_eligible=True,source='fixture://prices',fixture=True)])
    print((await agent.run(QueryRequest(session_id='demo',message='{"store_id":"s","sku_id":"shirt","as_of":"2026-01-02","discount_pct":10,"promotion_start":"2026-01-01","promotion_end":"2026-01-03"}'),RequestContext(session_id='demo',principal_id='fixture',role=Role.PRICING_ANALYST,store_ids=['s']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
