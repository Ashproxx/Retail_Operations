import asyncio
from app.agents.supply.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role
async def main():
    agent=Agent([dict(store_id='s',vendor_id='fixture-vendor',sku_id='shirt',observed_on='2026-01-01',promised_lead_days=2,observed_lead_days=[2,3,2],capacity=100,unit_cost='50',source='fixture://vendor',fixture=True)])
    print((await agent.run(QueryRequest(session_id='demo',message='{"store_id":"s","sku_id":"shirt","as_of":"2026-01-02","mode":"replenish","daily_demand":5,"stock_units":10}'),RequestContext(session_id='demo',principal_id='fixture',role=Role.STORE_MANAGER,store_ids=['s']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
