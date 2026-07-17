Implemented and committed `a89c891`.

Changed:
- `sim/experiments/hysteresis_runner.py`
  - State-carrying ascending/descending gamma runner using `SwarmKernel`.
  - Raw per-replicate/per-gamma JSON records, fingerprints, CLI.
- `tests/test_hysteresis_runner.py`
  - Verifies reverse starts from forward terminal fingerprint.
  - Verifies same-seed deterministic records.

Tests:
- Focused: `2 passed`
- Full: `42 passed, 1 xfailed`

Limitation: this runner records raw schedules only; it does not infer transitions or make hysteresis claims. Kernel behavior remains unchanged.
