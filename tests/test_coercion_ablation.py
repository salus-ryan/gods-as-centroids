import json

import pytest

from sim.experiments.coercion_ablation import collect_coercion_ablation, main
from sim.swarm_kernel import Config


def _records(seed=29):
    return collect_coercion_ablation(
        [0.0, 0.5], seed=seed, replicates=2, steps=3,
        config=Config(N=10, cluster_update_freq=2, steps_per_generation=10_000),
    )


def test_conditions_have_matched_initial_fingerprints_per_seed_and_gamma():
    records = _records()
    pairs = {}
    for record in records:
        pairs.setdefault((record["seed"], record["requested_gamma"]), []).append(record)

    for condition_records in pairs.values():
        assert {record["condition"] for record in condition_records} == {
            "null_gamma", "contact_homophily",
        }
        assert len({record["initial_state_fingerprint"] for record in condition_records}) == 1


def test_effective_gamma_is_condition_specific():
    for record in _records():
        if record["condition"] == "null_gamma":
            assert record["effective_gamma"] == 0.0
        else:
            assert record["effective_gamma"] == record["requested_gamma"]
        assert "raw_metrics" in record
        assert "state_fingerprint" in record


def test_collection_is_deterministic():
    assert _records(41) == _records(41)


def test_cli_writes_metadata_and_refuses_overwrite(tmp_path):
    output = tmp_path / "ablation.json"
    assert main([
        "--output", str(output), "--gammas", "0,0.5", "--replicates", "2",
        "--seed", "31", "--steps", "0", "--agents", "4",
    ]) == 0
    collection = json.loads(output.read_text(encoding="utf-8"))
    assert collection["metadata"]["conditions"] == ["null_gamma", "contact_homophily"]
    assert collection["metadata"]["measurement"]["gamma_independent"] is True
    assert collection["metadata"]["resolved_config"] == collection["config"]

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        main(["--output", str(output)])
