FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
WORKDIR /app
COPY requirements.txt requirements.txt
COPY app/rag/requirements.txt app/rag/requirements.txt
COPY app/orchestration/router/requirements.txt app/orchestration/router/requirements.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt
COPY app app
RUN useradd --uid 10001 --create-home retailops && mkdir /app/state && chown retailops:retailops /app/state
USER retailops
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
