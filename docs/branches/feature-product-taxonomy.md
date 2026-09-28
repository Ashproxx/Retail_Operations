# Product taxonomy

Purpose: configurable apparel normalization preserving raw values.
Owned: app/conversation/taxonomy.py, config/apparel_taxonomy.json, test_taxonomy.py.
Interfaces exposed: classify, normalize, mentioned_category; no database authority or writes.
Inputs: observed source category/attributes; explicit JSON mapping. Unknowns remain null and are flagged.
Deliverables: [x] mapping [x] raw preservation [x] conservative aliases [ ] Product 360 composition (core dependency).
Validation: taxonomy unit tests; no existing source module changed.
Baseline: b74a06df9753e7e20f66c4c6bb8874114fe50a9f.
Integration: consume from the conversation foundation; M2 requires Product 360 and integrated verification.
Knowledge delta: taxonomy config -> classify -> normalize -> Product 360; tests cover preservation and unknown values.
