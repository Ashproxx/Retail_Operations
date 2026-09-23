import asyncio
from app.agents.inventory.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role

async def main():
    agent=Agent([dict(store_id='fixture-store',sku_id='fixture-shirt',observed_on='2026-09-01',closing_stock=5,
       reorder_point=10,lead_days=3,daily_demand=4,source='fixture://inventory',fixture=True)])
    print((await agent.run(QueryRequest(message='{"as_of":"2026-09-02","action":"low_stock"}',session_id='demo'),
          RequestContext(session_id='demo',principal_id='fixture',role=Role.INVENTORY_MANAGER,store_ids=['fixture-store']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
