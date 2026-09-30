# Run the whole RetailOps website

Use Python 3.12. The frontend is included; Node and a separate frontend server are not needed. No real dataset, model download, cloud subscription or existing `.env` is required for the synthetic demo.

## Existing Windows checkout

Open PowerShell **in the folder containing `requirements.txt`**. Stop the old server with Ctrl+C. Save any personal code changes before switching branches; these commands do not discard changes.

```powershell
git fetch origin
git switch integration/conversational-retailops
git pull --ff-only
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.conversation.showcase
```

If Python is missing, install Python 3.12 from python.org, enable the launcher during setup, reopen PowerShell and check `py -3.12 --version`.

For a new checkout, run these first:

```powershell
git clone --branch integration/conversational-retailops https://github.com/Ashproxx/Retail_Operations.git
cd Retail_Operations
```

Open **http://127.0.0.1:8000/assistant?demo=1**. Click **Connect**, then paste the random temporary access token printed in that same terminal. There is no universal token. Keep the terminal open while using the website.

`init` is not needed for this demo. If an earlier `init` says “Configuration exists,” preserve that configuration and use the showcase command directly. It creates its own temporary database and token. Stopping the server deletes the demo database.

`127.0.0.1` means the laptop on which the browser runs. To demonstrate on another laptop, clone and start the application there too. A copied localhost link does not connect to the original laptop. A cancelled authentication dialog can be reopened with Connect. If port 8000 is busy, use `--port 8001` and open the printed link.

## Linux/macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.conversation.showcase
```

## Five-minute demonstration

1. Ask “Show today's sales.” Select **Bandra**. Only one missing selection is requested at a time.
2. Ask “What about last week?” The location is retained; dates use Asia/Kolkata.
3. Click **View graph**, then **pie**. The chart and interpretation use the same observed totals as the answer. Expand accessible chart data for exact values.
4. Ask “Why are shorts not selling?” Review the stock-constrained and declining product signals.
5. Ask “What should we do about it?” Review replenishment before promotions, evidence and limitations. No operation executes.
6. Ask “Who competes with it?” Review internal product comparisons. External competitor coverage is explicitly unavailable.
7. Ask “Forecast next 7 days.” See model selection, chronological MAE/RMSE and heuristic bands.
8. Start a new conversation and ask “Check my order in Bandra” or “Check pricing in Bandra.” Select the available purchase/product. These reuse the original authenticated agents.

The 120-day apparel series is synthetic and ends on the local business date. The retained operational demo records have their own disclosed historical observation dates. Neither is a real business dataset. The original `/dashboard` is also available; its older operations views use the original record formats, while `/assistant` uses the canonical observation layer.

## Own data and persistent configuration

Use the existing `app.integration.cli init` once only, then the explicit CSV/XLSX mapping importer described in [IMPORT.md](IMPORT.md). Start `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1` and open `/assistant`. Use your provisioned local token. This mode does not seed fixtures.

Policy retrieval and optional language-model classification use the existing local RAG/Ollama setup documented in the repository. The demo works deterministically without either. No policy citation is invented when retrieval is unavailable.
