import asyncio
import json
import httpx
import pytest
from app.integration.llm import OllamaProvider
from app.core.exceptions import ComponentUnavailableError


def test_ollama_protocol_local_draft():
    def handler(request):
        assert request.url.path=='/api/chat'
        body=json.loads(request.content)
        assert body['stream'] is False and body['model']=='local-test'
        assert len(body['messages'])==2
        return httpx.Response(200,json={'message':{'content':'Source-backed draft'}})
    provider=OllamaProvider('http://localhost:11434','local-test',transport=httpx.MockTransport(handler))
    assert asyncio.run(provider.draft('3 units'))=='Source-backed draft'

@pytest.mark.parametrize('response',[httpx.Response(503),httpx.Response(200,json={'unexpected':'secret'}),httpx.Response(200,json={'message':{'content':None}})])
def test_unavailable_or_malformed_provider(response):
    provider=OllamaProvider('http://localhost:11434','local-test',transport=httpx.MockTransport(lambda request:response))
    with pytest.raises(ComponentUnavailableError):asyncio.run(provider.draft('observed facts'))
