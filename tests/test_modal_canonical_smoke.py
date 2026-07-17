import json

import pytest

from sim.experiments.modal_canonical_smoke import (
    DEFAULT_SEED,
    SMOKE_STEPS,
    canonical_kernel_fingerprint,
    run_identical_seed_smoke,
)


def test_local_canonical_smoke_replays_and_is_json_safe():
    result = run_identical_seed_smoke(DEFAULT_SEED)

    assert result["identical"] is True
    assert result["seed"] == DEFAULT_SEED
    assert result["runs"][0]["steps"] == SMOKE_STEPS
    assert result["runs"][0]["terminal_state_sha256"] == result["runs"][1]["terminal_state_sha256"]
    assert result["provenance"]["canonical_kernel_module"] == "sim.swarm_kernel.SwarmKernel"
    assert result["provenance"]["canonical_kernel_sha256"] == canonical_kernel_fingerprint()
    json.dumps(result, allow_nan=False)


def test_smoke_fails_when_injected_same_seed_runs_diverge():
    calls = 0

    def divergent_run_once(seed):
        nonlocal calls
        calls += 1
        return {"seed": seed}, {"run": calls}

    with pytest.raises(AssertionError, match="identical-seed smoke run diverged"):
        run_identical_seed_smoke(7, run_once=divergent_run_once)
