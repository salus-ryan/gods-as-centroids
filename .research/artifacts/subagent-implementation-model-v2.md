Implemented and committed P0 model slice.

Changed:
- `sim/swarm_kernel.py`
- `tests/test_swarm_kernel_model.py`

Behavior decisions:
- Projection noise requires injected kernel RNG.
- `mutation_rate` is Gaussian belief-noise magnitude; `form_mutation_rate=0.08` preserves former form-mutation default.
- Unit vectors use normalized Gaussian samples over full sphere.
- Added deterministic simple undirected `random`, `small_world`, and `preferential` graphs.

Tests:
- `pytest -q tests/test_swarm_kernel_model.py` → `8 passed`
- `pytest -q` → `34 passed, 1 failed`  
  Existing legacy paper-claim test `test_high_coercion_monotheism` now fails (`D=0.10`); not altered per scope restriction on coercion/clustering.

Commit: `a3434033c48d056768a8a5543b99f4845e840f1a` (`Implement deterministic kernel mutation and network modes`)
