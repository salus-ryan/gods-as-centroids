import json

import pytest

from sim.experiments.modal_canonical_hysteresis_collection import (
    COLLECTION_VOLUME_MOUNT_PATH,
    canonical_kernel_sha256,
    collection_artifact_path,
    collection_sha256,
    collect_canonical_hysteresis,
    deserialize_collection,
    parse_gamma_schedule,
    serialize_collection,
    validate_collection_id,
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


def test_collection_id_is_uuid4_and_cannot_escape_volume_path():
    collection_id = "4f0dce79-9d19-4cdf-bc35-508fa95a5521"
    assert validate_collection_id(collection_id) == collection_id
    assert collection_artifact_path(collection_id) == (
        f"{COLLECTION_VOLUME_MOUNT_PATH}/{collection_id}.json"
    )

    for unsafe_id in (
        "../collection",
        "collection.json",
        "4F0DCE79-9D19-4CDF-BC35-508FA95A5521",
        "4f0dce79-9d19-3cdf-bc35-508fa95a5521",
        "4f0dce79-9d19-4cdf-7c35-508fa95a5521",
    ):
        with pytest.raises(ValueError):
            collection_artifact_path(unsafe_id)


def test_collection_serialization_is_json_safe_deterministic_and_checksummed():
    collection = {"records": [{"gamma": 0.5}], "metadata": {"seed": 41}}
    serialized = serialize_collection(collection)

    assert serialized == serialize_collection({"metadata": {"seed": 41}, "records": [{"gamma": 0.5}]})
    assert json.loads(serialized) == collection
    checksum = collection_sha256(serialized)
    assert deserialize_collection(serialized, checksum) == collection
    with pytest.raises(ValueError, match="checksum"):
        deserialize_collection(serialized, "0" * 64)
    with pytest.raises(ValueError):
        serialize_collection({"not_json": float("nan")})


def test_write_collection_is_non_overwriting(tmp_path):
    output = tmp_path / "raw.json"
    collection = _small_collection([0.0])

    assert write_collection(output, collection) == output
    assert json.loads(output.read_text(encoding="utf-8"))["records"] == collection["records"]
    with pytest.raises(FileExistsError):
        write_collection(output, collection)
