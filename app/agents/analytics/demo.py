import asyncio
from app.agents.analytics.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role
async def main():
    records=[dict(store_id='fixture-store',sku_id='shirt',category='shirts',day='2026-01-01',units_sold=3,unit_price_inr='200',closing_stock=2,reorder_point=5,source='fixture://sales',fixture=True)]
    print((await Agent(records).run(QueryRequest(session_id='demo',message='{"start":"2026-01-01","end":"2026-01-02"}'),RequestContext(session_id='demo',principal_id='fixture',role=Role.ANALYST,store_ids=['fixture-store']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
