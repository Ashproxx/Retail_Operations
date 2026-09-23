import subprocess,sys
BASE='77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def main():
    assert git('branch','--show-current')=='agent/pricing-promotions'
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    paths=set(git('diff','--name-only',BASE).splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    meta={'BRANCH_README.md','BRANCH_DELIVERABLES.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.md','docs/knowledge_graph/BRANCH_KNOWLEDGE_GRAPH.json'}
    bad=[x for x in paths if x not in meta and not x.startswith(('app/agents/pricing/','tests/pricing/'))]
    if bad:sys.exit(str(bad))
    print(f'PASS: {len(paths)} scoped paths')
if __name__=='__main__':main()
