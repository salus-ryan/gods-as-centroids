Implemented and committed sensory-success projection fix.

Changed files:
- `sim/swarm_kernel.py`
- `tests/test_swarm_kernel_model.py`

Behavior:
- Success now compares each hearer’s noisy observed context and interpreted message in the same channel-projected space.
- Channel noise is applied only to accessible observed-context axes via kernel RNG.
- Unrestricted agents retain full-space comparison.

Tests:
- `pytest -q tests/test_swarm_kernel_model.py` — 10 passed
- `pytest -q` — 36 passed, 1 xfailed

Known limitation:
- Existing overlapping-channel weighting semantics were retained; this slice only corrects the success comparison/noise scope.

Commit:
- `120e11c45bfab164ebe672ce0192ac121b1a3ca6`
