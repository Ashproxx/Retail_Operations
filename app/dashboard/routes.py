from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ASSETS = Path(__file__).parent / 'static'

def mount_dashboard(api):
    api.mount('/dashboard-assets', StaticFiles(directory=ASSETS), name='dashboard-assets')

    @api.get('/dashboard', include_in_schema=False)
    def dashboard():
        return FileResponse(ASSETS / 'index.html', headers={
            'Cache-Control': 'no-store',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            'X-Content-Type-Options': 'nosniff',
        })
