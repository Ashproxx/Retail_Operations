# Remaining-work validation

## Verified baseline

[GitHub Actions run 35878697558](https://github.com/Ashproxx/Retail_Operations/actions/runs/35878697558), commit `9e939b2519f314281cf246e224206aefa6eaff8d`, completed successfully. Job 107241234230 confirms CPU dependency installation, dependency check, source-preservation guard, full 178-test suite, offline demo, Compose configuration and Docker image build all passed. The earlier implementation run 35878477560 also succeeded.

## New measurements

Pending execution: actual pretrained MiniLM retrieval, actual Ollama inference, and non-root authenticated container/restart workflows. Scripts fail visibly rather than substituting mocks for these gates. CI preserves JSON reports containing model revision/digest, measured retrieval outcomes and container checks. No tokens, grants or raw real data are uploaded in artifacts.

Model choices are a routine local-development implementation decision under the user's approval to continue: free public CPU-capable models, no paid-service dependency, no change to the defined architecture. Sources: [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), [SmolLM2](https://ollama.com/library/smollm2:135m), [Ollama v0.34.3](https://github.com/ollama/ollama/releases/tag/v0.34.3).

## Scope of claims

The retrieval set has 12 labelled positive queries, six authored documents and two unanswerable questions; every record is synthetic. It measures a development regression set, not held-out production recall or calibrated answer quality. Live Ollama only establishes functioning local transport/inference, with an unverified draft kept separate from facts. The small model is not claimed to be a reliable retail reasoning system.

Real retail dataset mapping and validation remain outstanding because no such dataset was supplied. Do not mark M13 PASS or replace absent observations with synthetic production results.
