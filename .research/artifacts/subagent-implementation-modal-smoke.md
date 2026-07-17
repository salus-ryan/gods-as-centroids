Implemented and committed canonical Modal smoke test.

- Commit: `86bfc29a4bdced5c00d7a8b054f6e2edc6f38639`
- Files:
  - `sim/experiments/modal_canonical_smoke.py`
  - `tests/test_modal_canonical_smoke.py`

Invocation:
```bash
modal run sim/experiments/modal_canonical_smoke.py
```

It uploads/imports `sim.swarm_kernel.SwarmKernel`, runs a tiny fixed config twice with the same seed, returns JSON-safe provenance/snapshot hashes, and raises on divergence. Core is callable without Modal.

Tests:
```bash
pytest -q tests/test_modal_canonical_smoke.py  # 2 passed
pytest -q                                  # 55 passed, 5 xfailed
```

Also validated Modal entrypoint discovery:
```bash
modal run sim/experiments/modal_canonical_smoke.py --help
```

Limitation: did not submit the remote Modal job (avoids external compute/auth dependency).
