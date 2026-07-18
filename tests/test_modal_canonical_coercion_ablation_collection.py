import json

import pytest

from sim.experiments.modal_canonical_coercion_ablation_collection import (
    COLLECTION_VOLUME_MOUNT_PATH,
    DEFAULT_REPLICATES,
    DEFAULT_REQUESTED_GAMMAS,
    DEFAULT_STEPS,
    canonical_kernel_sha256,
    collection_artifact_path,
    collection_sha256,
    collection_volume_relative_path,
    collect_canonical_coercion_ablation,
    deserialize_collection,
    parse_requested_gammas,
    serialize_collection,
    validate_collection_id,
    write_collection,
)
from sim.swarm_kernel import Config


def _small_collection(gammas="0,0.5,1"):
    return collect_canonical_coercion_ablation(
        gammas=gammas,
        replicates=2,
        steps=0,
        seed=41,
        config=Config(N=4, cluster_update_freq=1),
    )


def test_defaults_and_local_core_return_all_raw_condition_records():
    assert DEFAULT_REPLICATES == 12
    assert DEFAULT_REQUESTED_GAMMAS == tuple(round(index / 10, 1) for index in range(11))
    assert DEFAULT_STEPS == 500
    assert parse_requested_gammas("0, 0.5,1") == [0.0, 0.5, 1.0]

    collection = _small_collection()
    assert len(collection["records"]) == 2 * 3 * 2
    assert collection["metadata"]["schedule"] == {
        "requested_gammas": [0.0, 0.5, 1.0],
        "steps": 0,
    }
    assert {record["condition"] for record in collection["records"]} == {
        "null_gamma", "contact_homophily",
    }


def test_condition_pairs_retain_identical_initial_state_fingerprints():
    pairs = {}
    for record in _small_collection()["records"]:
        key = (record["replicate"], record["seed"], record["requested_gamma"])
        pairs.setdefault(key, []).append(record)

    assert len(pairs) == 2 * 3
    for records in pairs.values():
        assert len(records) == 2
        assert {record["condition"] for record in records} == {
            "null_gamma", "contact_homophily",
        }
        assert len({record["initial_state_fingerprint"] for record in records}) == 1


def test_metadata_is_complete_and_explicitly_disclaims_causal_inference():
    collection = _small_collection([0.0])
    metadata = collection["metadata"]
    provenance = metadata["provenance"]

    assert metadata["replicate_count"] == 2
    assert metadata["seed_scheme"]["base_seed"] == 41
    assert metadata["resolved_config"] == collection["config"]
    assert metadata["conditions"] == ["null_gamma", "contact_homophily"]
    assert metadata["measurement"]["gamma_independent"] is True
    assert "no causal inference is made" in metadata["collection_purpose"]
    assert provenance["canonical_kernel_module"] == "sim.swarm_kernel.SwarmKernel"
    assert provenance["canonical_kernel_sha256"] == canonical_kernel_sha256()
    assert provenance["canonical_collector_callable"] == "collect_coercion_ablation"


def test_serialization_is_deterministic_strict_json_and_checksummed():
    collection = {"records": [{"requested_gamma": 0.5}], "metadata": {"seed": 41}}
    serialized = serialize_collection(collection)

    assert serialized == serialize_collection({
        "metadata": {"seed": 41}, "records": [{"requested_gamma": 0.5}],
    })
    assert json.loads(serialized) == collection
    checksum = collection_sha256(serialized)
    assert deserialize_collection(serialized, checksum) == collection
    with pytest.raises(ValueError, match="checksum"):
        deserialize_collection(serialized, "0" * 64)
    with pytest.raises(ValueError):
        serialize_collection({"not_json": float("nan")})


def test_collection_id_is_lowercase_uuid4_and_path_safe():
    collection_id = "4f0dce79-9d19-4cdf-bc35-508fa95a5521"
    assert validate_collection_id(collection_id) == collection_id
    assert collection_volume_relative_path(collection_id) == f"{collection_id}.json"
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


def test_write_collection_exclusively_persists_raw_artifact(tmp_path):
    output = tmp_path / "raw.json"
    collection = _small_collection([0.0])

    assert write_collection(output, collection) == output
    assert json.loads(output.read_text(encoding="utf-8")) == collection
    with pytest.raises(FileExistsError):
        write_collection(output, collection)
