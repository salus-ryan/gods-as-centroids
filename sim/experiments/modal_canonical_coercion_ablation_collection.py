"""Modal launcher for raw canonical matched-state coercion ablations.

This module only collects evidence.  The condition labels and behavior come from
``sim.experiments.coercion_ablation``; the resulting records do not establish a
causal effect and must not be interpreted as causal inference.

Run the remote function directly when detaching (generate a fresh lowercase
UUID4 for every collection)::

    modal run --detach sim/experiments/modal_canonical_coercion_ablation_collection.py::remote_collect \
      --collection-id 4f0dce79-9d19-4cdf-bc35-508fa95a5521

After it completes, download the durable, checksummed Volume artifact with::

    modal volume get canonical-coercion-ablation-raw-collections \
      4f0dce79-9d19-4cdf-bc35-508fa95a5521.json coercion-ablation-raw.json
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable
import uuid

from sim.experiments.coercion_ablation import CONDITIONS, collect_coercion_ablation
from sim.experiments.hysteresis_runner import experiment_metadata
from sim.swarm_kernel import Config

DEFAULT_REPLICATES = 12
DEFAULT_STEPS = 500
DEFAULT_SEED = 202503
DEFAULT_REQUESTED_GAMMAS = tuple(round(index / 10, 1) for index in range(11))
COLLECTION_VOLUME_NAME = "canonical-coercion-ablation-raw-collections"
COLLECTION_VOLUME_MOUNT_PATH = "/collections"
_UUID4_COLLECTION_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def validate_collection_id(collection_id: str) -> str:
    """Validate a path-safe canonical lowercase UUID4 collection ID."""
    if not isinstance(collection_id, str) or not _UUID4_COLLECTION_ID.fullmatch(collection_id):
        raise ValueError("collection_id must be a canonical lowercase UUID4")
    if uuid.UUID(collection_id).version != 4:
        raise ValueError("collection_id must be a UUID4")
    return collection_id


def collection_volume_relative_path(collection_id: str) -> str:
    return f"{validate_collection_id(collection_id)}.json"


def collection_artifact_path(collection_id: str) -> str:
    return f"{COLLECTION_VOLUME_MOUNT_PATH}/{collection_volume_relative_path(collection_id)}"


def serialize_collection(collection: dict[str, Any]) -> bytes:
    """Return deterministic strict-JSON bytes used both for storage and hashing."""
    return (json.dumps(collection, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def collection_sha256(serialized_collection: bytes) -> str:
    return hashlib.sha256(serialized_collection).hexdigest()


def deserialize_collection(
    serialized_collection: bytes, expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify an optional remote checksum and decode one collection artifact."""
    if expected_sha256 is not None and collection_sha256(serialized_collection) != expected_sha256:
        raise ValueError("persisted collection checksum does not match remote metadata")
    decoded = json.loads(serialized_collection.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("persisted collection must be a JSON object")
    return decoded


def parse_requested_gammas(gammas: str | Iterable[float]) -> list[float]:
    """Normalize the CLI representation while rejecting invalid requested values."""
    try:
        values = (
            [part.strip() for part in gammas.split(",") if part.strip()]
            if isinstance(gammas, str)
            else list(gammas)
        )
        parsed = [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise ValueError("gammas must be a comma-separated string or numeric iterable") from exc
    if not parsed:
        raise ValueError("gammas must contain at least one value")
    if any(not math.isfinite(gamma) or gamma < 0.0 for gamma in parsed):
        raise ValueError("gammas must be finite and non-negative")
    return parsed


def canonical_kernel_sha256() -> str:
    """Digest the exact canonical kernel source uploaded with this launcher."""
    source = Path(__file__).resolve().parents[1] / "swarm_kernel.py"
    return hashlib.sha256(source.read_bytes()).hexdigest()


def collect_canonical_coercion_ablation(
    *,
    replicates: int = DEFAULT_REPLICATES,
    steps: int = DEFAULT_STEPS,
    seed: int = DEFAULT_SEED,
    gammas: str | Iterable[float] = DEFAULT_REQUESTED_GAMMAS,
    config: Config | None = None,
) -> dict[str, Any]:
    """Use the canonical collector and return unaggregated records plus metadata."""
    requested_gammas = parse_requested_gammas(gammas)
    if replicates < 1:
        raise ValueError("replicates must be at least one")
    if steps < 0:
        raise ValueError("steps must be non-negative")

    resolved_config = copy.deepcopy(config) if config is not None else Config()
    resolved_config.seed = seed
    resolved_config.coercion = 0.0
    records = collect_coercion_ablation(
        requested_gammas,
        replicates=replicates,
        seed=seed,
        steps=steps,
        config=resolved_config,
    )
    metadata = experiment_metadata(
        resolved_config, requested_gammas, steps, replicates, seed,
    )
    metadata.update({
        "schedule": {"requested_gammas": requested_gammas, "steps": steps},
        "conditions": list(CONDITIONS),
        "measurement": {
            "cluster_method": "fixed kernel cluster configuration",
            "gamma_independent": True,
        },
        "collection_purpose": (
            "Raw matched-state ablation evidence only; these observational simulation "
            "records do not establish causation and no causal inference is made."
        ),
        "provenance": {
            "canonical_kernel_module": "sim.swarm_kernel.SwarmKernel",
            "canonical_kernel_sha256": canonical_kernel_sha256(),
            "canonical_collector_module": "sim.experiments.coercion_ablation",
            "canonical_collector_callable": "collect_coercion_ablation",
            "condition_source": "sim.experiments.coercion_ablation.CONDITIONS",
        },
    })
    collection: dict[str, Any] = {
        "config": asdict(resolved_config),
        "metadata": metadata,
        "records": records,
    }
    serialize_collection(collection)
    return collection


def write_collection(output: str | Path, collection: dict[str, Any]) -> Path:
    """Exclusively persist evidence, refusing to replace an existing artifact."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as destination:
        destination.write(serialize_collection(collection))
    return path


try:  # The local collection and serialization core does not depend on Modal.
    import modal
except ImportError:  # pragma: no cover - expected in lean local environments
    modal = None


if modal is not None:
    app = modal.App("canonical-coercion-ablation-raw-collection")
    collection_volume = modal.Volume.from_name(COLLECTION_VOLUME_NAME, create_if_missing=True)
    image = modal.Image.debian_slim(python_version="3.11").add_local_dir(
        local_path=str(Path(__file__).resolve().parents[1]), remote_path="/root/sim",
    )

    @app.function(
        image=image,
        timeout=3600,
        cpu=1,
        volumes={COLLECTION_VOLUME_MOUNT_PATH: collection_volume},
    )
    def remote_collect(
        collection_id: str,
        replicates: int = DEFAULT_REPLICATES,
        steps: int = DEFAULT_STEPS,
        seed: int = DEFAULT_SEED,
        # A plain comma-delimited string is safe for Modal's generated CLI.
        gammas: str = ",".join(str(value) for value in DEFAULT_REQUESTED_GAMMAS),
    ) -> dict[str, Any]:
        """Exclusively commit a raw artifact and return its checksum metadata."""
        from sim.experiments.coercion_ablation import collect_coercion_ablation as remote_collector
        from sim.experiments.modal_canonical_coercion_ablation_collection import (
            collection_artifact_path,
            collection_sha256,
            collection_volume_relative_path,
            collect_canonical_coercion_ablation,
            serialize_collection,
        )

        assert remote_collector is not None  # Make the canonical remote dependency explicit.
        collection = collect_canonical_coercion_ablation(
            replicates=replicates, steps=steps, seed=seed, gammas=gammas,
        )
        artifact_path = collection_artifact_path(collection_id)
        serialized = serialize_collection(collection)
        with Path(artifact_path).open("xb") as artifact:
            artifact.write(serialized)
        collection_volume.commit()
        checksum = collection_sha256(serialized)
        return {
            "collection_id": collection_id,
            "volume_name": COLLECTION_VOLUME_NAME,
            "container_path": artifact_path,
            "volume_relative_path": collection_volume_relative_path(collection_id),
            "checksum": checksum,
            "sha256": checksum,
        }

    @app.local_entrypoint()
    def main(
        output: str,
        collection_id: str,
        replicates: int = DEFAULT_REPLICATES,
        steps: int = DEFAULT_STEPS,
        seed: int = DEFAULT_SEED,
        gammas: str = ",".join(str(value) for value in DEFAULT_REQUESTED_GAMMAS),
    ) -> None:
        """Copy the verified Volume artifact locally; never trust a return payload."""
        artifact = remote_collect.remote(collection_id, replicates, steps, seed, gammas)
        serialized = b"".join(collection_volume.read_file(artifact["volume_relative_path"]))
        collection = deserialize_collection(serialized, artifact["checksum"])
        write_collection(output, collection)
