import subprocess
import sys
BASE='77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045'
META={'BRANCH_README.md','BRANCH_DELIVERABLES.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.json'}

def git(*args):return subprocess.check_output(['git',*args],text=True).strip()

def main():
    if git('branch','--show-current')!='agent/router':sys.exit('FAIL: expected agent/router')
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    files=set(git('diff','--name-only',BASE).splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    bad=[f for f in files if f not in META and not f.startswith(('app/orchestration/router/','tests/router/'))]
    if bad:sys.exit('FAIL: outside router scope '+str(bad))
    print(f'PASS: {len(files)} router-only paths')

if __name__=='__main__':main()
