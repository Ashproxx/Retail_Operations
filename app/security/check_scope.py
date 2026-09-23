import subprocess,sys
BASE='77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045'
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def main():
    assert git('branch','--show-current')=='security/privacy-integrity'
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    files=set(git('diff','--name-only',BASE).splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    meta={'BRANCH_README.md','BRANCH_DELIVERABLES.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.json'}
    bad=[f for f in files if f not in meta and not f.startswith(('app/security/','tests/security/'))]
    if bad:sys.exit('FAIL: '+str(bad))
    print(f'PASS: {len(files)} security-only paths')
if __name__=='__main__':main()
