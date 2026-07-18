Implemented and committed the Modal coercion-ablation collection wrapper.

- Module: `sim/experiments/modal_canonical_coercion_ablation_collection.py`
- Tests: `tests/test_modal_canonical_coercion_ablation_collection.py`
- Full suite: **70 passed, 5 xfailed**
- Commit: `b7defe5`

Detached invocation:

```bash
modal run --detach sim/experiments/modal_canonical_coercion_ablation_collection.py::remote_collect \
  --collection-id <lowercase-uuid4>
```

Download artifact:

```bash
modal volume get canonical-coercion-ablation-raw-collections \
  <lowercase-uuid4>.json coercion-ablation-raw.json
```
