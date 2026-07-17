Implemented and committed v2 transmission slice.

- Per-child, prestige-weighted distinct mentor sets.
- Child beliefs are normalized averages of own mentors.
- Lexicon mixing is per child.
- Channels inherit from deterministic highest-prestige mentor (ID tie-break).
- Child prestige resets to `1.0`; IDs remain `0..N-1`.
- Graph rebuilds; clustering state is reset and recomputed for children.
- Added mentor provenance and deterministic transmission tests.

Changed:
- `sim/swarm_kernel.py`
- `tests/test_swarm_kernel_model.py`

Tests:
- Focused: `18 passed`
- Full: `47 passed, 4 xfailed`

Note: an earlier full run had one stochastic legacy paper-claim failure (`test_high_alpha_fewer_centroids`); its isolated rerun and final full rerun passed.

Limitation: exactly cancelling mentor beliefs fall back to the first selected mentor rather than creating non-inherited randomness.

Commit: `0ff69e5`
