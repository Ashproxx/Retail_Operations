import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def test_local_provisioning_secret_hygiene_and_no_overwrite(tmp_path):
    env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[2])}
    command=[sys.executable,'-m','app.integration.cli','init']
    result=subprocess.run(command,cwd=tmp_path,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    token=(tmp_path/'secrets/admin-token.txt').read_text().strip()
    grants=json.loads((tmp_path/'secrets/grants.json').read_text())
    assert len(token)>=32 and token not in result.stdout+result.stderr
    assert grants[0]['token_sha256']==hashlib.sha256(token.encode()).hexdigest()
    assert 'RETAILOPS_INTEGRITY_KEY=' in (tmp_path/'.env').read_text()
    second=subprocess.run(command,cwd=tmp_path,env=env,capture_output=True,text=True)
    assert second.returncode!=0
    assert (tmp_path/'secrets/admin-token.txt').read_text().strip()==token
    if os.name=='posix':assert (tmp_path/'secrets/admin-token.txt').stat().st_mode & 0o777==0o600
