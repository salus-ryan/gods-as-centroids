Implemented and committed Modal-backed canonical launcher.

- Commit: `15b4ed5 feat: add Modal canonical hysteresis collection launcher`
- Tests: `58 passed, 5 xfailed`
- Defaults: 12 replicates, γ=0.0…1.0 by 0.1, 500 steps/γ.
- Outputs raw JSON-safe records with metadata and canonical kernel SHA; explicitly states evidence-only/no hysteresis inference.
- Non-overwriting `--output` writer included.

Exact detached invocation:

```bash
modal run --detach sim/experiments/modal_canonical_hysteresis_collection.py --output hysteresis-raw.json
```
