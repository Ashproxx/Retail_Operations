"""Offline plan-only demo: no downstream agent runs or business data."""
import asyncio
import json
from app.api.schemas import QueryRequest,RequestContext,Role
from app.orchestration.router.agent import RouterAgent


async def main():
    router=RouterAgent()
    for message in ['Which products are below their reorder point?',
                    'Inventory is low but demand is increasing and should we change the price?',
                    'Please help with something unusual']:
        result=await router.run(QueryRequest(message=message,session_id='fixture-demo'),
            RequestContext(session_id='fixture-demo',principal_id='fixture-user',role=Role.ANALYST))
        print(json.dumps({'query':message,'status':result.status,'plan':result.data['plan']},indent=2))


if __name__=='__main__': asyncio.run(main())
