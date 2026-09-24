"""Rebuild the integrated code index; no changes to archived source records."""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    nodes={};edges=[]
    def node(id,kind,**meta):nodes[id]={'id':id,'type':kind,**meta}
    def edge(a,b,kind):edges.append({'source':a,'target':b,'type':kind})
    manifest=json.loads((ROOT/'docs/integration/APPROVED_SOURCES.json').read_text())
    node('integration/release-candidate','branch',base=manifest['base'])
    for source in manifest['sources']:
        node(source['branch'],'branch',commit=source['sha'])
        edge(source['branch'],'integration/release-candidate','approved_for_integration')
    node('M13','milestone',status='INCOMPLETE',weighted_completion=95)
    edge('integration/release-candidate','M13','implements')
    paths=sorted([*ROOT.glob('app/**/*.py'),*ROOT.glob('tests/**/*.py'),*ROOT.glob('scripts/*.py')])
    modules={str(p.relative_to(ROOT))[:-3].replace('/','.'):str(p.relative_to(ROOT)) for p in paths}
    for path in paths:
        relative=str(path.relative_to(ROOT))
        node(relative,'test' if relative.startswith('tests/') else 'file')
        edge('integration/release-candidate',relative,'contains')
        tree=ast.parse(path.read_text())
        for item in tree.body:
            if isinstance(item,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                id=relative+'::'+item.name
                node(id,'class' if isinstance(item,ast.ClassDef) else 'function')
                edge(relative,id,'defines')
            if isinstance(item,ast.ImportFrom) and item.module in modules:edge(relative,modules[item.module],'imports')
        if relative.startswith('tests/'):
            for item in ast.walk(tree):
                if isinstance(item,ast.ImportFrom) and item.module in modules and item.module.startswith('app.'):
                    edge(relative,modules[item.module],'tests')
    routes=ast.parse((ROOT/'app/integration/routes.py').read_text())
    for item in routes.body:
        if isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for d in item.decorator_list:
                if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.args and isinstance(d.args[0],ast.Constant):
                    id=d.func.attr.upper()+' /api'+d.args[0].value
                    node(id,'API endpoint');edge(id,'app/integration/routes.py::'+item.name,'implemented_by')
    for table in ['domain_records','stores','session_state','request_receipts','signed_rag_manifest']:
        node(table,'database table');edge('app/integration/repository.py',table,'reads_writes')
    for id,path in [('authorization','app/security/policy.py'),('signed_evidence','app/integration/rag.py'),('audit_chain','app/security/audit.py')]:
        node(id,'security control');edge(id,path,'implemented_by');edge('app/integration/orchestrator.py',id,'protected_by')
    node('evaluation/retail_rag_fixture.json','dataset',fixture=True,positive_queries=12,negative_queries=2)
    node('evaluation/models.json','model registry',pinned=True)
    edge('scripts/evaluate_retrieval.py','evaluation/retail_rag_fixture.json','evaluates_on')
    edge('scripts/download_evaluation_model.py','evaluation/models.json','reads')
    edge('scripts/evaluate_retrieval.py','app/integration/rag.py','tests')
    edge('scripts/container_smoke.py','app/main.py','tests')
    edge('scripts/live_ollama_smoke.py','app/integration/llm.py','tests')
    dashboard_paths = sorted(ROOT.glob('app/dashboard/static/*')) + [ROOT/'scripts/check_dashboard.cjs']
    for path in dashboard_paths:
        relative = str(path.relative_to(ROOT))
        node(relative, 'browser test' if path.suffix == '.cjs' else 'dashboard asset')
        edge('integration/release-candidate', relative, 'contains')
    node('GET /dashboard', 'UI endpoint')
    edge('GET /dashboard', 'app/dashboard/routes.py', 'implemented_by')
    edge('app/dashboard/routes.py', 'app/dashboard/static/index.html', 'serves')
    edge('app/dashboard/static/index.html', 'app/dashboard/static/app.js', 'loads')
    edge('app/dashboard/static/index.html', 'app/dashboard/static/style.css', 'loads')
    for endpoint in ['POST /api/chat', 'POST /api/query', 'POST /api/feedback', 'GET /api/audit']:
        edge('app/dashboard/static/app.js', endpoint, 'calls_with_bearer')
    edge('scripts/check_dashboard.cjs', 'GET /dashboard', 'tests')
    edge('app/integration/showcase.py', 'app/dashboard/fixtures.py', 'explicit_synthetic_seed')
    payload={'scope':'human-approved integration candidate','status':'M13 INCOMPLETE / 95%','nodes':list(nodes.values()),'edges':edges}
    folder=ROOT/'docs/knowledge_graph'
    for name in ['MASTER_KNOWLEDGE_GRAPH.json','BRANCH_KNOWLEDGE_GRAPH.json']:(folder/name).write_text(json.dumps(payload,indent=2)+'\n')
    intro=f'# Integrated knowledge graph\n\n{len(nodes)} nodes / {len(edges)} edges. M13 INCOMPLETE; 95% weighted completion. See `docs/integration/REPORT.md` for validation and blockers. Source records are immutable under `docs/integration/sources/`; their milestone statements are historical.\n\n'
    body=(ROOT/'ARCHITECTURE.md').read_text()
    extra='''\n## Branch ownership\n\n```mermaid\nflowchart TD\n foundation[Pinned foundation] --> agents[Approved agent commits]\n foundation --> platform[Approved RAG commit]\n foundation --> security[Approved security commit]\n agents --> integration[Integration candidate]\n platform --> integration\n security --> integration\n integration --> shared[Shared adapters and API wiring]\n shared --> qa[Full QA and review]\n```\n\n## Test relationships\n\n```mermaid\nflowchart TD\n unit[Original branch suites] --> domains[Domain logic and contracts]\n api[Integration API tests] --> orchestration[Auth execution and memory]\n storage[Storage tests] --> sql[Atomic imports and scope]\n evidence[RAG integration tests] --> signed[Signed Chroma evidence]\n provider[Provider tests] --> ollama[Ollama protocol and fallback]\n domains --> full[Full candidate suite]\n orchestration --> full\n sql --> full\n signed --> full\n ollama --> full\n```\n'''
    for name in ['MASTER_KNOWLEDGE_GRAPH.md','BRANCH_KNOWLEDGE_GRAPH.md']:(folder/name).write_text(intro+body+extra)
    ownership=['# Integrated file ownership','', '| Path | Integration owner |','|---|---|']
    for path in paths + dashboard_paths:ownership.append(f'| `{path.relative_to(ROOT)}` | integration/release-candidate; original source ownership preserved in archives |')
    (folder/'FILE_OWNERSHIP_MAP.md').write_text('\n'.join(ownership)+'\n')
    (folder/'DATA_FLOW_GRAPH.md').write_text('# Data flow\n\nSee the implemented system, multi-agent, RAG and security flows in [ARCHITECTURE.md](../../ARCHITECTURE.md).\n\nCSV/XLSX -> explicit mapping -> domain validation -> transactional SQL -> authorized records -> domain result -> conflict/aggregation -> audit -> response.\n')
    (folder/'INTERFACE_REGISTRY.md').write_text('''# Integrated interface registry

| Interface | Purpose |
|---|---|
| `ChatQuery`, `DirectQuery` | No client-controlled role; parameters validated by selected domain contract |
| `RequestContext` | Server-owned identity, role, store scope and request ID |
| `REGISTRY` / `contracts` | Router IDs -> domain classes and authorization actions |
| `Repository.records` | Authorized SQL record access before domain execution |
| `TabularLoader.load` | Explicit CSV/XLSX mapping and atomic record validation |
| `Orchestrator.run` | LangGraph dispatch, conflict handling, memory and audit |
| `SignedRag.query/ingest` | Trusted scope and HMAC manifest around the original vector store |
| `Provider.draft` | Optional unverified narrative; no tool execution authority |
| `AuditChain.append/read` | Metadata chain, single writer, externally retained anchor required |

Exact definitions are indexed in the machine-readable graph. Original branch contracts remain unchanged.
''')
    (folder/'BRANCH_GRAPH.md').write_text('# Approved branch lineage\n\nBase: '+manifest['base']+'\n\n'+ '\n'.join(f"- `{s['branch']}` @ `{s['sha']}`" for s in manifest['sources'])+'\n\nOnly integration/release-candidate may be written. Main and source branch refs remain unchanged. Remote publication uses an approved multi-parent integration commit so every source commit remains an ancestor.\n')
    (folder/'TEST_COVERAGE_MAP.md').write_text('''# Test coverage map

| Suite | Behavior |
|---|---|
| tests/foundation | Schemas, SQL lifecycle, health, error hygiene; endpoint expectations updated for integration |
| tests/router and tests/<domain> | Original routing and eight domain suites, unchanged |
| tests/rag, tests/security | Original local retrieval, integrity and role suites, unchanged |
| tests/integration/test_api.py | All agent IDs, seven prompt queries, follow-up isolation/revocation, aggregation/conflicts, feedback, audit, errors |
| tests/integration/test_storage.py | CSV/XLSX atomic mapping, dates, formulas, duplicates, invalid stock, authorization before DB |
| tests/integration/test_rag.py | Real local Chroma and sentence-transformers fixture, rehashed tampering, manifest corruption, support/API integration |
| tests/integration/test_dashboard.py | Dashboard serving, authenticated synthetic showcase, preserved configuration and empty normal startup |
| tests/integration/test_provider.py | Mocked Ollama wire protocol and unavailable/malformed responses |

Extended real-dependency checks: scripts/evaluate_retrieval.py (pinned pretrained MiniLM and labelled synthetic cases), scripts/live_ollama_smoke.py (actual Ollama inference), scripts/container_smoke.py (non-root container and restart workflows).\n\nMeasured evidence: [validation report](../integration/VALIDATION.md) and docs/integration/measurements/. The authored synthetic set is not production-quality certification.
''')
    print(f'Indexed {len(nodes)} nodes / {len(edges)} edges')

if __name__=='__main__':main()
