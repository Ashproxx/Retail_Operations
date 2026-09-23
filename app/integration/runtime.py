import json
from pathlib import Path
from app.security.policy import Grant, TokenAuthenticator
from app.security.audit import AuditChain
from app.core.exceptions import ComponentUnavailableError
from app.integration.config import RuntimeSettings
from app.integration.repository import Repository
from app.integration.rag import LazyRag
from app.integration.llm import provider_for
from app.integration.orchestrator import Orchestrator

class Runtime:
    def __init__(self,database,config:RuntimeSettings,*,grants=None,rag=None,provider=None):
        self.config=config
        config.state_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
        if grants is None:
            grants=[] if config.grants_file is None else [Grant.model_validate(g) for g in json.loads(config.grants_file.read_text())]
        self.auth=TokenAuthenticator(grants)
        self.repository=Repository(database)
        self.audit=AuditChain(config.state_dir/'audit.jsonl')
        # Fail startup if the current log is malformed. Cross-restart rollback detection
        # still requires an independently retained trusted anchor (documented).
        self.audit.read()
        self.rag=rag or LazyRag(database,config)
        try:self.provider=provider or provider_for(config)
        except ComponentUnavailableError:self.provider=None
        self.orchestrator=Orchestrator(self.repository,self.audit,self.rag,self.provider)
