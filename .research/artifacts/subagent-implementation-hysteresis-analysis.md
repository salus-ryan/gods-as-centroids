Implemented and committed deterministic analyzer.

Commit: `7998f43 Add canonical hysteresis collection analyzer`

Added:
- `sim/experiments/modal_canonical_hysteresis_analysis.py`
- `tests/test_modal_canonical_hysteresis_analysis.py`

Validated focused and full tests:
- `pytest -q tests/test_modal_canonical_hysteresis_analysis.py`
- `pytest -q` → `64 passed, 5 xfailed`

Analyze a downloaded raw collection with:

```bash
python -m sim.experiments.modal_canonical_hysteresis_analysis \
  --input hysteresis-raw.json \
  --output hysteresis-analysis.json
```
