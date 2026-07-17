Implemented and committed P0 reproducibility slice.

Changed:
- `sim/run.py`
  - Strict plain-object config loading.
  - Unknown keys now fail.
  - Corpus-calibrated wrapper fails with conversion guidance.
  - Added immutable `provenance.json` with resolved config, steps, seed, git revision, Python, and platform metadata.
- `tests/test_run.py`
  - Covers valid config application, unknown keys, corpus wrapper rejection, and provenance fields.

Tests:
- Focused: `pytest -q tests/test_run.py` → 4 passed
- Full: `pytest -q` → 40 passed, 1 xfailed

Commit:
- `d604b84 Add strict run config provenance`

Limitation: corpus-calibrated wrapper conversion is intentionally not implemented in this bounded slice; callers must explicitly convert it to a plain `Config` JSON object.
