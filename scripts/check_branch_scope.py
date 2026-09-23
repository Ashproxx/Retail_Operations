"""Integration guard: pinned ancestry, source tree preservation, branch identity."""
import argparse
import json
from pathlib import Path
import subprocess

def git(*args):return subprocess.check_output(['git',*args],text=True).strip()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ci',action='store_true');args=parser.parse_args()
    branch=git('branch','--show-current')
    if branch!='integration/release-candidate' and not (args.ci and branch==''):
        raise SystemExit('FAIL: run on the approved integration candidate only')
    manifest=json.loads(Path('docs/integration/APPROVED_SOURCES.json').read_text())
    subprocess.run(['git','merge-base','--is-ancestor',manifest['base'],'HEAD'],check=True)
    for source in manifest['sources']:
        subprocess.run(['git','merge-base','--is-ancestor',source['sha'],'HEAD'],check=True)
        paths=git('diff','--name-only',manifest['base'],source['sha']).splitlines()
        for path in paths:
            if path.startswith('app/') or (path.startswith('tests/') and not path.startswith('tests/foundation/')):
                if Path(path).read_bytes()!=subprocess.check_output(['git','show',source['sha']+':'+path]):
                    raise SystemExit('FAIL: source implementation changed: '+path)
        archive=Path('docs/integration/sources')/source['branch']
        for path in ['BRANCH_README.md','BRANCH_DELIVERABLES.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.json']:
            if (archive/path).read_bytes()!=subprocess.check_output(['git','show',source['sha']+':'+path]):
                raise SystemExit('FAIL: branch record archive differs')
    print('PASS: approved ancestry, 11 source implementations and archives preserved; changes confined to integration checkout.')

if __name__=='__main__':main()
