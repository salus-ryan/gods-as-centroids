Implemented and committed detached Modal persistence.

- Named Volume: `canonical-hysteresis-raw-collections`
- UUID4-safe collection IDs and collision-safe exclusive artifact writes
- Remote metadata includes volume name/path/checksum
- Local copies read and checksum-verify the committed Volume artifact
- Added serialization/path-safety tests
- Full tests: `60 passed, 5 xfailed`
- Commit: `f8a18c7`

Detached run:
```bash
modal run --detach sim/experiments/modal_canonical_hysteresis_collection.py::remote_collect \
  --collection-id 4f0dce79-9d19-4cdf-bc35-508fa95a5521
```

Monitor:
```bash
modal app list
modal app logs <app-id>
```

Download:
```bash
modal volume get canonical-hysteresis-raw-collections \
  collections/4f0dce79-9d19-4cdf-bc35-508fa95a5521.json hysteresis-raw.json
```
