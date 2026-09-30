# Product taxonomy

Purpose: configurable apparel normalization preserving raw values.
Owned: app/conversation/taxonomy.py, config/apparel_taxonomy.json, test_taxonomy.py.
Interfaces exposed: classify, normalize, mentioned_category; no database authority or writes.
Inputs: observed source category/attributes; explicit JSON mapping. Unknowns remain null and are flagged.
Deliverables: [x] mapping [x] raw preservation [x] conservative aliases [x] Product 360 composition (core dependency).
Validation: taxonomy unit tests; no existing source module changed.
Baseline: b74a06df9753e7e20f66c4c6bb8874114fe50a9f.
Integration: consume from the conversation foundation; M2 requires Product 360 and integrated verification.
Knowledge delta: taxonomy config -> classify -> normalize -> Product 360; tests cover preservation and unknown values.

Integrated verification (2026-09-30): local Python suite and both real-browser gates passed. See `docs/conversation/VALIDATION.md` for tested scope and commit evidence. Feature checkpoints remain unchanged; this annotation belongs to the integration candidate.

Remote feature/checkpoint SHA: `1b8b3602a38b7e7befaf865fdd731b989b177f05`. Integration verification target: `c613603e503f675d9da2651d05e3af07438f54f1`; final CI evidence is recorded in `docs/conversation/VALIDATION.md`.
