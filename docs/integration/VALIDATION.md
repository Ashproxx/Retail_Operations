# Remaining-work validation

## Verified baseline

[GitHub Actions run 35878697558](https://github.com/Ashproxx/Retail_Operations/actions/runs/35878697558), commit `9e939b2519f314281cf246e224206aefa6eaff8d`, completed successfully. Job 107241234230 confirms CPU dependency installation, dependency check, source-preservation guard, full 178-test suite, offline demo, Compose configuration and Docker image build all passed. The earlier implementation run 35878477560 also succeeded.

## New measurements

Pretrained MiniLM retrieval completed locally: 12/12 expected documents ranked first (recall@3 also 12/12), 8/12 evidence answers, four conservative paraphrase abstentions, 2/2 unrelated-question abstentions and zero scope leaks. See `measurements/retrieval.json` for every labelled outcome. Actual Ollama and container/restart checks now pass in the expanded CI rerun. Scripts fail visibly rather than substituting mocks for these gates. CI preserves JSON reports containing model revision/digest, measured retrieval outcomes and container checks. No tokens, grants or raw real data are uploaded in artifacts.

Model choices are a routine local-development implementation decision under the user's approval to continue: free public CPU-capable models, no paid-service dependency, no change to the defined architecture. Sources: [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), [SmolLM2](https://ollama.com/library/smollm2:135m), [Ollama v0.34.3](https://github.com/ollama/ollama/releases/tag/v0.34.3).

## Scope of claims

The retrieval set has 12 labelled positive queries, six authored documents and two unanswerable questions; every record is synthetic. It measures a development regression set, not held-out production recall or calibrated answer quality. Live Ollama only establishes functioning local transport/inference, with an unverified draft kept separate from facts. The small model is not claimed to be a reliable retail reasoning system.

Real retail dataset mapping and validation remain outstanding because no such dataset was supplied. Do not mark M13 PASS or replace absent observations with synthetic production results.

## First expanded CI run

Run 35908353883 at `285a36697f7788706325d30e5da1983cb7c2b94b` passed all 178 tests, Docker build, pinned-model download, pretrained retrieval, and real Ollama inference. It also passed initial non-root container health, authentication, missing data, authorized query, scope denial and container-to-Ollama drafting before failing the post-restart health probe. The smoke harness used Docker's initial randomly assigned host port after restart; the follow-up change refreshes that mapping and adds container state/log diagnostics. The rerun must pass before claiming restart persistence.

Ollama result: version 0.34.3, model smollm2:135m, digest `9077fe9d2ae1a4a41a868836b56b8163731a8fe16621397028c2c76f838c6907`, non-empty actual inference. See `measurements/ollama.json`. No generated-answer factuality claim is made.

## Successful expanded rerun

[Run 35909119561](https://github.com/Ashproxx/Retail_Operations/actions/runs/35909119561) at `8d0d2b444a6cc3382f11bc3720000e7c93ba1f26` completed SUCCESS. Job 107344177255 passed every step. The corrected restart probe resolves Docker's newly assigned ephemeral port. Non-root UID 10001, initial health, missing-token rejection, empty database, authorized fixture query, denied store query, live Ollama draft, restart persistence, remembered follow-up intent and owned feedback all passed. An independent local runtime teardown/reinitialization also preserved data, memory, feedback receipts and the valid audit chain.

Measurements are preserved in `measurements/retrieval.json`, `measurements/ollama.json` and `measurements/container.json`. Artifact 10772063773 has ZIP digest `sha256:9ac52368d5731d638f0cfef503a37c585d6f30b8c7d97f9bc22b09323495e1ea`. The live inference server was Ollama 0.34.3; exact model and container image digests are recorded.

The sole remaining data-dependent completion gap is the user's actual retail CSV/XLSX, its explicit column mapping and expected business-output checks. The backend can be run and its fixture demo used now; it is neither deployed to Azure nor merged into main.
