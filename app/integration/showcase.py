"""Explicit localhost-only showcase with disposable synthetic data and credentials."""
import argparse
import hashlib
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
import uvicorn
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.dashboard.fixtures import seed_showcase
from app.security.policy import Grant


def showcase_app(directory, token):
    directory = Path(directory)
    config = RuntimeSettings(_env_file=None,
        database_url='sqlite+pysqlite:///' + str(directory / 'showcase.db'),
        state_dir=directory / 'state', grants_file=None, integrity_key=None,
        embedding_model_path=None, llm_provider='deterministic')
    grant = Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),
                  principal_id='showcase-admin', role='ADMIN')

    def factory(database, settings):
        runtime = Runtime(database, settings, grants=[grant])
        seed_showcase(runtime.repository)
        return runtime

    return create_app(config, factory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    token = secrets.token_urlsafe(32)
    with TemporaryDirectory(prefix='retailops-showcase-') as directory:
        print('\nRetailOps showcase | SYNTHETIC DATA | September 9–22, 2026')
        print(f'Open http://127.0.0.1:{args.port}/dashboard?demo=1')
        print('Paste this temporary access token into the dashboard connection dialog:')
        print(token, flush=True)
        print('This database is deleted when the server stops. No real orders are placed.\n', flush=True)
        uvicorn.run(showcase_app(directory, token), host='127.0.0.1', port=args.port)

if __name__ == '__main__':
    main()
