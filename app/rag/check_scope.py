"""RAG-only change guard relative to the pinned foundation."""
import subprocess
import sys
BASE = '77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045'
META = {'BRANCH_README.md','BRANCH_DELIVERABLES.md',
        'docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.md',
        'docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.json'}

def git(*args):
    return subprocess.check_output(['git', *args],text=True).strip()

def main():
    if git('branch','--show-current') != 'platform/agentic-rag':
        sys.exit('FAIL: expected platform/agentic-rag')
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    paths=set(git('diff','--name-only',BASE).splitlines())
    paths.update(git('ls-files','--others','--exclude-standard').splitlines())
    bad=[p for p in paths if p not in META and not p.startswith(('app/rag/','tests/rag/'))]
    if bad:sys.exit('FAIL: outside RAG scope: '+str(bad))
    print(f'PASS: {len(paths)} RAG-only changed paths')

if __name__=='__main__': main()
