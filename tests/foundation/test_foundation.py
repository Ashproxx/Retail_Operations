import asyncio
import json
import logging
from uuid import uuid4, UUID
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text
from app.main import create_app
from app.core.config import Settings
from app.core.exceptions import ComponentUnavailableError, DataValidationError, NotFoundError
from app.core.logging import MetadataFormatter
from app.api.schemas import AgentResult, AuditEvent, QueryRequest, RequestContext, Role
from app.agents.base_agent import BaseAgent
from app.services.database_service import Database
from app.services.dataset_loader import DatasetLoader


def test_configuration_reads_environment_and_hides_credentials(monkeypatch):
    monkeypatch.setenv('RETAILOPS_DATABASE_URL', 'postgresql://user:secret@localhost/retail')
    monkeypatch.setenv('RETAILOPS_MAX_RAG_ITERATIONS', '4')
    settings = Settings(_env_file=None)
    assert settings.max_rag_iterations == 4
    assert 'secret' not in repr(settings)


@pytest.mark.parametrize('settings', [{'max_rag_iterations': 0}, {'routing_confidence_threshold': 1.1}, {'log_level': 'invalid'}])
def test_invalid_configuration(settings):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **settings)


@pytest.mark.parametrize('payload', [
    {'message': ' ', 'session_id': 's'},
    {'message': 'hello', 'session_id': ''},
    {'message': 'hello', 'session_id': 's', 'role': 'ADMIN'},
    {'message': 'x' * 4001, 'session_id': 's'},
])
def test_reject_invalid_or_privilege_claiming_payload(payload):
    with pytest.raises(ValidationError):
        QueryRequest(**payload)


def test_agent_contract_and_collection_isolation():
    class EchoAgent(BaseAgent):
        async def run(self, query, context):
            return AgentResult(agent='test', request_id=context.request_id, status='success',
                               summary=query.message, confidence=1)
    context = RequestContext(session_id='s', principal_id='test-only', role=Role.ANALYST)
    result = asyncio.run(EchoAgent().run(QueryRequest(message='hello', session_id='s'), context))
    other = result.model_copy(deep=True)
    result.warnings.append('test')
    assert other.warnings == []
    assert result.request_id == context.request_id
    assert result.summary == 'hello'
    with pytest.raises(TypeError):
        BaseAgent()


@pytest.mark.parametrize('value', [-0.1, 1.1, float('nan'), float('inf')])
def test_agent_confidence_bounds(value):
    with pytest.raises(ValidationError):
        AgentResult(agent='test', request_id=uuid4(), status='success', summary='', confidence=value)


def test_audit_has_timezone_and_rejects_raw_payload():
    event = AuditEvent(request_id=uuid4(), session_id='s', user_role=Role.ANALYST,
                       confidence=0, latency_ms=0, final_status='escalated')
    assert event.timestamp.tzinfo is not None
    with pytest.raises(ValidationError):
        AuditEvent(**event.model_dump(), raw_document='private')


def test_transaction_commit_rollback_and_parameter_binding(tmp_path):
    db = Database('sqlite+pysqlite:///' + str(tmp_path / 'test.db'))
    try:
        assert db.ping()
        with db.session() as session:
            session.execute(text('CREATE TABLE fixtures (name TEXT)'))
        malicious = "x'); DROP TABLE fixtures; --"
        with db.session() as session:
            session.execute(text('INSERT INTO fixtures VALUES (:name)'), {'name': malicious})
        with pytest.raises(RuntimeError):
            with db.session() as session:
                session.execute(text('INSERT INTO fixtures VALUES (:name)'), {'name': 'rollback'})
                raise RuntimeError('simulate failure')
        with db.session() as session:
            assert session.execute(text('SELECT name FROM fixtures')).scalars().all() == [malicious]
    finally:
        db.close()


def test_dataset_contract_paths(tmp_path):
    with pytest.raises(TypeError):
        DatasetLoader()
    with pytest.raises(NotFoundError):
        DatasetLoader.validate_source(tmp_path / 'missing.csv')
    with pytest.raises(DataValidationError):
        DatasetLoader.validate_source(tmp_path / 'unsafe.exe')
    source = tmp_path / 'fixture.csv'
    source.write_text('sku_id\nfixture-only\n')
    assert DatasetLoader.validate_source(source) == source


def test_logging_drops_payload_and_exception_details():
    record = logging.LogRecord('retailops', logging.ERROR, '', 1, 'secret-password', (), None)
    record.event = 'agent_failure'
    record.document = 'private-document'
    formatted = MetadataFormatter().format(record)
    assert 'secret-password' not in formatted
    assert 'private-document' not in formatted
    assert json.loads(formatted)['event'] == 'agent_failure'


def test_health_root_and_openapi():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        assert client.get('/').json()['stage'] == 'integration-candidate'
        health = client.get('/health')
        assert health.status_code == 200
        assert health.json()['database'] == 'ok'
        UUID(health.headers['X-Request-ID'])
        assert '/health' in client.get('/openapi.json').json()['paths']
        assert client.get('/docs').status_code == 200
        assert client.post('/api/chat', json={'message': 'hello', 'session_id':'test'}).status_code == 401


def test_health_reports_database_failure(monkeypatch):
    api = create_app(Settings(_env_file=None))
    with TestClient(api) as client:
        def fail():
            raise RuntimeError('secret connection details')
        monkeypatch.setattr(api.state.database, 'ping', fail)
        response = client.get('/health')
        assert response.status_code == 503
        assert 'secret' not in response.text


def test_future_adapter_errors_and_validation():
    api = create_app(Settings(_env_file=None))
    # Test-only routes; no domain endpoint is shipped on the foundation branch.
    @api.post('/test-contract')
    def contract(query: QueryRequest):
        return query
    @api.get('/test-unavailable')
    def unavailable():
        raise ComponentUnavailableError('secret source details')
    @api.get('/test-unexpected')
    def unexpected():
        raise RuntimeError('secret token')
    with TestClient(api, raise_server_exceptions=False) as client:
        assert client.post('/test-contract', json={'message': 'hello', 'session_id': 's'}).status_code == 200
        response = client.post('/test-contract', json={'message': '', 'session_id': 's', 'private': 'secret'})
        assert response.status_code == 422
        assert 'secret' not in response.text
        assert response.json()['code'] == 'invalid_request'
        for route, status in [('/test-unavailable', 503), ('/test-unexpected', 500)]:
            response = client.get(route)
            assert response.status_code == status
            assert 'secret' not in response.text
            assert response.json()['request_id'] == response.headers['X-Request-ID']
