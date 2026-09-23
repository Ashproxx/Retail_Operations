import asyncio
from datetime import date,timedelta
from app.agents.forecasting.agent import Agent
from app.api.schemas import QueryRequest,RequestContext,Role
async def main():
    rows=[dict(store_id='fixture-store',sku_id='shirt',day=date(2026,1,1)+timedelta(days=i),units=10+i%7,source='fixture://sales',fixture=True) for i in range(28)]
    print((await Agent(rows).run(QueryRequest(session_id='demo',message='{"store_id":"fixture-store","sku_id":"shirt","as_of":"2026-01-28"}'),RequestContext(session_id='demo',principal_id='fixture',role=Role.ANALYST,store_ids=['fixture-store']))).model_dump_json(indent=2))
if __name__=='__main__':asyncio.run(main())
