import json

import pytest

from sim.experiments.modal_canonical_hysteresis_collection import (
    canonical_kernel_sha256,
    collect_canonical_hysteresis,
    parse_gamma_schedule,
    write_collection,
)
from sim.swarm_kernel import Config


def _small_collection(gammas="0,0.5,1"):
    return collect_canonical_hysteresis(
        gammas=gammas,
        replicates=2,
        steps_per_gamma=0,
        seed=41,
        config=Config(N=4, cluster_update_freq=1),
    )


def test_local_core_accepts_comma_and_list_schedules_and_returns_raw_records():
    assert parse_gamma_schedule("0, 0.5,1") == [0.0, 0.5, 1.0]
    assert parse_gamma_schedule([0, 0.5, 1]) == [0.0, 0.5, 1.0]

    collection = _small_collection()
    assert collection["metadata"]["gamma_schedule"] == [0.0, 0.5, 1.0]
    assert len(collection["records"]) == 2 * 2 * 3
    assert [record["gamma"] for record in collection["records"][:3]] == [0.0, 0.5, 1.0]
    assert [record["gamma"] for record in collection["records"][3:6]] == [1.0, 0.5, 0.0]
    json.dumps(collection, allow_nan=False)


def test_local_core_records_canonical_provenance_without_hysteresis_inference():
    collection = _small_collection([0.0])
    metadata = collection["metadata"]
    provenance = metadata["provenance"]

    assert provenance["canonical_kernel_module"] == "sim.swarm_kernel.SwarmKernel"
    assert provenance["canonical_kernel_sha256"] == canonical_kernel_sha256()
    assert provenance["canonical_runner_callable"] == "run_hysteresis_schedule"
    assert "do not infer hysteresis" in metadata["collection_purpose"]
    assert metadata["replicate_count"] == 2
    assert len(collection["records"]) == 4


def test_write_collection_is_non_overwriting(tmp_path):
    output = tmp_path / "raw.json"
    collection = _small_collection([0.0])

    assert write_collection(output, collection) == output
    assert json.loads(output.read_text(encoding="utf-8"))["records"] == collection["records"]
    with pytest.raises(FileExistsError):
        write_collection(output, collection)
