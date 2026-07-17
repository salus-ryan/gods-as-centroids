import hashlib
import json
import pickle

import pytest

from sim.experiments.hysteresis_runner import main, run_hysteresis_schedule, state_fingerprint
from sim.swarm_kernel import Config


def _records(seed=19):
    return run_hysteresis_schedule(
        [0.0, 0.5, 1.0],
        seed=seed,
        steps_per_gamma=3,
        config=Config(
            N=10,
            cluster_update_freq=2,
            steps_per_generation=10_000,
            mutation_rate=0.02,
        ),
    )


def test_descending_branch_starts_at_exact_forward_terminal_state():
    records = _records()
    forward = [record for record in records if record["direction"] == "ascending"]
    descending = [record for record in records if record["direction"] == "descending"]

    assert descending[0]["gamma"] == forward[-1]["gamma"]
    assert descending[0]["starting_state_fingerprint"] == forward[-1]["state_fingerprint"]


def test_records_are_deterministic_for_same_seed():
    assert _records(41) == _records(41)


def test_cli_writes_complete_reproducibility_metadata(tmp_path):
    output = tmp_path / "collection.json"

    assert main([
        "--output", str(output), "--gammas", "0,0.5", "--steps-per-gamma", "0",
        "--replicates", "2", "--seed", "31", "--agents", "4",
    ]) == 0

    collection = json.loads(output.read_text(encoding="utf-8"))
    metadata = collection["metadata"]
    assert metadata["gamma_schedule"] == [0.0, 0.5]
    assert metadata["steps_per_gamma"] == 0
    assert metadata["replicate_count"] == 2
    assert metadata["seed_scheme"] == {
        "base_seed": 31, "per_replicate": "base_seed + replicate_index",
    }
    assert metadata["resolved_config"] == collection["config"]
    assert "git_revision" in metadata
    assert metadata["python"]["version"]
    assert metadata["platform"]["platform"]
    assert metadata["terminal_state_artifacts"] == []


def test_cli_terminal_state_artifacts_are_checksummed(tmp_path):
    output = tmp_path / "collection.json"
    main([
        "--output", str(output), "--gammas", "0", "--steps-per-gamma", "0",
        "--agents", "4", "--serialize-terminal-states",
    ])

    collection = json.loads(output.read_text(encoding="utf-8"))
    artifact = collection["metadata"]["terminal_state_artifacts"][0]
    artifact_path = output.parent / artifact["path"]
    payload = artifact_path.read_bytes()
    assert artifact["format"] == "pickle"
    assert artifact["sha256"] == hashlib.sha256(payload).hexdigest()
    assert state_fingerprint(pickle.loads(payload)) == collection["records"][-1]["state_fingerprint"]


def test_cli_refuses_to_overwrite_existing_output(tmp_path):
    output = tmp_path / "collection.json"
    output.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        main(["--output", str(output), "--steps-per-gamma", "0"])

    assert output.read_text(encoding="utf-8") == "existing"
