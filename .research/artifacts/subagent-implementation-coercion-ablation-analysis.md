Implemented and committed deterministic coercion-ablation analysis.

- Added `sim/experiments/modal_canonical_coercion_ablation_analysis.py`
- Added focused tests in `tests/test_modal_canonical_coercion_ablation_analysis.py`
- Full suite: `74 passed, 5 xfailed`
- Commit: `4b10392 Add descriptive coercion ablation analyzer`

CLI:

```bash
python -m sim.experiments.modal_canonical_coercion_ablation_analysis \
  --input coercion-ablation-raw.json \
  --output coercion-ablation-report.json
```

Output files are created exclusively; existing outputs are never overwritten.
