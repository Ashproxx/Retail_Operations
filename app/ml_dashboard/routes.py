import json
import hashlib
from pathlib import Path
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.schemas import Role
from app.integration.routes import context, audit_operation
from app.ml_dashboard.quality import observation_coverage

ASSETS = Path(__file__).parent/'static'


def evidence(reports, filename):
    manifest = json.loads((reports/'manifest.json').read_text(encoding='utf-8'))
    data = (reports/filename).read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest[filename]['sha256']:
        raise ValueError('Evidence checksum mismatch')
    return json.loads(data)


def scoped_report(report, ctx):
    if ctx.role not in {Role.ADMIN, Role.ANALYST, Role.STORE_MANAGER}:
        raise HTTPException(403, 'This role cannot view retail model results.')
    admin = ctx.role == Role.ADMIN
    def permitted(row):
        if not isinstance(row, dict):
            raise ValueError('Invalid evidence row')
        series = row.get('series', [])
        return admin or len(series) == 2 and series[0] == 'store' and series[1] in ctx.store_ids
    return {'source_label': report['source_label'], 'code_commit': report['code_commit'],
        'curves': [r for r in report['curves'] if permitted(r)],
        'decisions': [r for r in report['decisions'] if permitted(r)],
        'leaderboard': report['leaderboard'] if admin else [],
        'test_failures': [r for r in report['test_failures'] if permitted(r)],
        'excluded_by_level': report['excluded_by_level'] if admin else None,
        'limitations': report['limitations'], 'global_summary_allowed': admin}


def install(api, reports=Path('validation-output/ml-dashboard')):
    reports = Path(reports)
    api.mount('/ml-assets', StaticFiles(directory=ASSETS), name='ml-assets')
    @api.get('/ml', include_in_schema=False)
    def page():
        return FileResponse(ASSETS/'index.html', headers={'Cache-Control':'no-store',
            'X-Content-Type-Options':'nosniff', 'Content-Security-Policy':
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})

    @api.get('/api/ml/results')
    def results(request: Request):
        ctx = context(request, 'ml-dashboard')
        status = 'denied'
        try:
            if ctx.role not in {Role.ADMIN, Role.ANALYST, Role.STORE_MANAGER}:
                raise HTTPException(403, 'This role cannot view retail model results.')
            try:
                report = evidence(reports, 'forecast.json')
                data = scoped_report(report, ctx)
                data['auxiliary'] = evidence(reports, 'auxiliary.json') if ctx.role == Role.ADMIN else None
                data['supplement'] = evidence(reports, 'supplement.json') if ctx.role == Role.ADMIN else None
            except (OSError, ValueError, KeyError, TypeError):
                raise HTTPException(503, 'Verified research reports are unavailable. Export the pinned evidence locally.') from None
            data['live'] = {'connected': hasattr(request.app.state, 'realtime'),
                            'message': 'Live observations are separate from frozen research results.'}
            data['data_quality'] = observation_coverage(request.app.state.runtime.repository.database, ctx)
            status = 'success'
            return JSONResponse(data, headers={'Cache-Control': 'no-store'})
        finally:
            audit_operation(request.app.state.runtime, ctx, 'ml.results', status)
