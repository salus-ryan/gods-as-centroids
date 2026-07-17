Implemented and committed `ceedfb1 feat: add raw coercion ablation collector`.

Added:
- `sim/experiments/coercion_ablation.py`
  - Programmatic `collect_coercion_ablation` API
  - Matched baseline fingerprints per `(seed, gamma)`
  - `null_gamma` and `contact_homophily` conditions
  - Raw metrics, requested/effective gamma, fingerprints, metadata, non-overwriting CLI JSON
- `tests/test_coercion_ablation.py`

Validation:
- Focused tests: `9 passed`
- Full pytest: `53 passed, 4 xfailed, 1 failed`
  - Existing unrelated failure: `tests/test_paper_claims.py::TestPrestigeConvergence::test_high_alpha_fewer_centroids`
