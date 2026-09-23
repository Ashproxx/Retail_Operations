from pathlib import Path
from pydantic import Field, SecretStr
from app.core.config import Settings

class RuntimeSettings(Settings):
    database_url: SecretStr = SecretStr('sqlite+pysqlite:///./retailops.db')
    state_dir: Path = Path('.retailops')
    grants_file: Path | None = None
    integrity_key: SecretStr | None = None
    embedding_model_path: Path | None = None
    embedding_identity: str = ''
    ollama_url: str = 'http://localhost:11434'
    ollama_model: str = ''
    llm_timeout_seconds: float = Field(default=20,gt=0,le=120)
