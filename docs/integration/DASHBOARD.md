# Interactive dashboard and today's showcase

The dashboard is served by the same FastAPI process at `/dashboard`. It uses the existing authenticated API; charts and tables are populated from API responses, not hard-coded browser metrics. No Node installation, frontend build, CDN, external font, or cloud API key is needed to run it.

## Windows: showcase without real data

Stop the previous server with Ctrl+C. From the existing repository folder:

```powershell
git switch integration/release-candidate
git pull --ff-only
.\.venv\Scripts\python.exe -m app.integration.showcase
```

Open `http://127.0.0.1:8000/dashboard?demo=1`. Paste the temporary access token printed in the terminal into **Connect workspace**. Keep the terminal running. If port 8000 is occupied, use `--port 8001` and open the matching URL.

The opt-in launcher binds to 127.0.0.1, creates a disposable SQLite database, seeds three stores / six product lines with synthetic records, and creates a temporary administrator grant. It does not read the existing `.env` or overwrite operational data. All data, feedback and audit events from this showcase disappear when the process stops. The token remains in browser memory only; refresh requires reconnection. Never publish the token. This mode is for a local presentation, not deployment.

## Suggested five-minute presentation

1. **Overview:** show observed sales, units, available stock and reorder signals. Point out the synthetic-data banner and fixed September 9–22, 2026 reporting period.
2. Change the store to `ANDHERI`; the cards, store chart and inventory fetch new backend results. Clear the store field to restore all authorized stores.
3. **Inventory:** toggle low stock only, compare cover and suggested replenishment quantities. Recommendations are advisory, not executed orders.
4. **Demand forecast:** use `BANDRA`, `SHIRT-1`, and the default September 22 date. Generate the seven-day forecast; show the uncalibrated uncertainty warning.
5. **Operations assistant:** ask “Which products are low in Bandra?” then “What about Andheri?” Expand the evidence, parameters and warnings. Try the inventory + demand suggestion and record feedback.
6. **Activity & audit:** load the administrator audit history to show the backend requests that produced the presentation.

Inventory and analytics fixtures cover all three stores. Other domain fixtures cover the original Bandra / O1 scenarios; unsupported questions or missing records correctly request clarification. The showcase runs deterministic agents, not a downloaded LLM. RAG model configuration and real data validation remain separate requirements.

## Use the existing operational backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Open `/dashboard` and connect with your existing local bearer token. The normal app never seeds records. Empty databases show missing evidence; permissions still apply to each operation. Enter your store ID and appropriate reporting dates. Refresh clears credentials, disconnect clears rendered data, and a new chat starts a separate backend session. `/docs`, `/health`, and the JSON `/` endpoint remain available.

## Implementation and validation

- `app/dashboard/static/`: responsive same-origin UI; safe text rendering, explicit loading/error/empty states, in-memory token, content security policy.
- `app/dashboard/routes.py`: static assets and dashboard document.
- `app/dashboard/fixtures.py`: explicit synthetic showcase records, isolated from normal startup.
- `app/integration/showcase.py`: localhost-only disposable launcher.
- `tests/integration/test_dashboard.py`: authentication, static serving, fixture data, forecast and preservation of existing configuration; normal startup remains empty.

Local Python suite: **180 passed**. One upstream Starlette/AnyIO deprecation warning. An initial environment restoration installed CUDA PyTorch and failed during native import; reinstalling CPU PyTorch restored the full passing run. No application workaround or test skip was used. Source preservation guard passes. Browser validation results are recorded below when completed.

M13 real-data validation remains incomplete; synthetic showcase results are not production accuracy evidence.
