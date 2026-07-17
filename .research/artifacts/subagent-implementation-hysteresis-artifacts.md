Implemented and committed reproducibility slice.

- Changed: `sim/experiments/hysteresis_runner.py`, `tests/test_hysteresis_runner.py`
- Added metadata, Git/runtime details, optional terminal pickle artifacts + SHA-256, exclusive output/artifact collision protection, and tests.
- Tests: focused `5 passed`; full `50 passed, 4 xfailed`.
- Commit: `efbccb141a9c088f7f70e913c51866547da14c5e`
- Limitation: terminal pickle files are trusted-local, code-version-dependent artifacts—not portable or safe for untrusted input.
