"""Opt-in local router audit sink; no raw queries or source documents."""
from pathlib import Path
from threading import Lock
from app.api.schemas import AuditEvent


class JsonlAuditSink:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()

    def __call__(self, event: AuditEvent) -> None:
        with self._lock:
            with self.path.open('a', encoding='utf-8') as stream:
                stream.write(event.model_dump_json() + '\n')
