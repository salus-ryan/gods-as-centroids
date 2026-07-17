Implemented and committed `b4c9009`.

Design:
- Threshold clustering is deterministic connected components over pairwise cosine-distance edges.
- Labels persist via deterministic maximum-overlap matching.
- Exchange counts agent A↔B label transitions across recent cluster-epoch snapshots.
- Fusion requires fixed centroid proximity (`0.15`) and positive exchange meeting threshold; zero exchange never fuses.
- Fission preserves one deterministic parent label and assigns a fresh sibling label.

Changed:
- `sim/swarm_kernel.py`
- `tests/test_swarm_kernel_model.py`

Tests:
- Focused: `16 passed`
- Full: `47 passed, 2 xfailed`

Limitations:
- Exchange is measured only at cluster epochs, not individual interaction events.

