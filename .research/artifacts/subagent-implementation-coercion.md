Implemented and committed P0 coercion slice.

Changed:
- `sim/swarm_kernel.py`
  - Coercion now affects only contact-homophily selection.
  - Cluster and fusion thresholds are gamma-independent.
  - Removed gamma-driven centroid-attractor pull.
- `tests/test_swarm_kernel_model.py`
  - Added deterministic tests for gamma-invariant clustering and gamma-sensitive homophilous contact selection.

Tests:
- Focused: `12 passed`
- Full: `41 passed, 1 failed, 1 xfailed`
  - Legacy failure retained: `TestPhaseTransitions::test_coercion_reduces_neff`, which asserts the removed direct coercion-to-clustering outcome.

Limitation:
- Fusion/fission mechanics otherwise remain unchanged; no institutional-pull model was introduced.

Commit: `b6e86aa model: confine coercion to contact homophily`
