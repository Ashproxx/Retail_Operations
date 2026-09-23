"""Test the built image as a non-root service with ephemeral synthetic state."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
from tempfile import TemporaryDirectory
import time
import urllib.error
import urllib.request


def docker(*args):
    return subprocess.check_output(['docker',*args],text=True).strip()

def request(base,path,token=None,payload=None):
    headers={}
    if token:headers['Authorization']='Bearer '+token
    data=None
    if payload is not None:data=json.dumps(payload).encode();headers['Content-Type']='application/json'
    with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers=headers),timeout=150) as response:
        return json.load(response)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--image',default='retailops-candidate')
    parser.add_argument('--with-ollama',action='store_true');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    name='retailops-smoke-'+secrets.token_hex(5);volume=name+'-state'
    token=secrets.token_urlsafe(32)
    with TemporaryDirectory() as temporary:
        directory=Path(temporary);directory.chmod(0o755)
        grants=directory/'grants.json'
        grants.write_text(json.dumps([{'token_sha256':hashlib.sha256(token.encode()).hexdigest(),
            'principal_id':'fixture-smoke','role':'STORE_MANAGER','store_ids':['BANDRA','ANDHERI']}]))
        grants.chmod(0o644) # Contains only a hash of this short-lived random fixture token.
        spec=json.loads(Path('evaluation/models.json').read_text())['ollama']
        options=['run','--detach','--name',name,'--publish','127.0.0.1::8000',
            '--mount',f'type=volume,source={volume},target=/app/state',
            '--mount',f'type=bind,source={grants.resolve()},target=/app/grants.json,readonly',
            '--env','RETAILOPS_GRANTS_FILE=/app/grants.json',
            '--env','RETAILOPS_DATABASE_URL=sqlite+pysqlite:////app/state/retailops.db',
            '--env','RETAILOPS_STATE_DIR=/app/state','--env','RETAILOPS_LLM_TIMEOUT_SECONDS=120']
        if args.with_ollama:options+=['--add-host','host.docker.internal:host-gateway','--env','RETAILOPS_OLLAMA_URL=http://host.docker.internal:11434',
                                    '--env','RETAILOPS_OLLAMA_MODEL='+spec['model']]
        else:options+=['--env','RETAILOPS_LLM_PROVIDER=deterministic']
        try:
            docker(*options,args.image)
            port=docker('port',name,'8000/tcp').split(':')[-1];base='http://127.0.0.1:'+port
            def ready():
                for _ in range(60):
                    try:
                        if request(base,'/health')['status']=='ok':return
                    except (OSError,ValueError):pass
                    time.sleep(1)
                state=docker('inspect','--format','{{.State.Status}} / exit {{.State.ExitCode}}',name)
                print('Container state at health failure:',state)
                subprocess.run(['docker','logs','--tail','50',name],check=False)
                raise RuntimeError('Container health timeout')
            ready()
            assert docker('exec',name,'id','-u')=='10001'
            try:request(base,'/api/chat',payload={'message':'inventory','session_id':'smoke'})
            except urllib.error.HTTPError as exc:assert exc.code==401
            else:raise AssertionError('Unauthenticated request accepted')
            empty=request(base,'/api/chat',token,{'message':'inventory','session_id':'smoke'})
            assert empty['data']['results']['inventory']['status']=='not_found'
            docker('exec',name,'python','-c',
                'from app.integration.config import RuntimeSettings; from app.services.database_service import Database; '
                'from app.integration.repository import Repository; from app.integration.fixtures import seed; '
                'db=Database(RuntimeSettings().database_url.get_secret_value()); seed(Repository(db)); db.close()')
            result=request(base,'/api/chat',token,{'message':'low stock in Bandra','session_id':'smoke','draft_with_llm':args.with_ollama})
            assert result['data']['status']=='success' and result['data']['fixture']
            if args.with_ollama:assert result['data'].get('unverified_llm_draft'),result['data'].get('llm_warning')
            denied=request(base,'/api/query',token,{'agent':'inventory','session_id':'smoke','parameters':{'store_id':'FORBIDDEN'}})
            assert denied['data']['results']['inventory']['data']['reason']=='access_denied'
            docker('restart',name)
            # Docker may allocate a new ephemeral host port when the container restarts.
            port=docker('port',name,'8000/tcp').split(':')[-1]
            base='http://127.0.0.1:'+port
            ready()
            follow=request(base,'/api/chat',token,{'message':'What about Andheri?','session_id':'smoke'})
            assert follow['data']['status']=='success'
            assert follow['data']['results']['inventory']['data']['items'][0]['store_id']=='ANDHERI'
            feedback=request(base,'/api/feedback',token,{'request_id':result['data']['request_id'],'session_id':'smoke','rating':1})
            assert feedback['recorded']
            report={'fixture':True,'image':args.image,'image_id':docker('image','inspect','--format','{{.Id}}',args.image),
                'nonroot_uid':10001,'startup':'PASS','authentication':'PASS','empty_database':'PASS','authorized_query':'PASS',
                'scope_denial':'PASS','restart_persistence':'PASS','followup_memory':'PASS','owned_feedback':'PASS',
                'live_ollama_draft':'PASS' if args.with_ollama else 'NOT_REQUESTED'}
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
        finally:
            subprocess.run(['docker','rm','--force',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            subprocess.run(['docker','volume','rm',volume],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

if __name__=='__main__':main()
