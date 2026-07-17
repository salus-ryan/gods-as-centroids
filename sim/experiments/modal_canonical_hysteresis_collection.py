"""Modal launcher for raw canonical hysteresis-schedule collections.

This launcher collects state-carrying schedule measurements as evidence.  It
intentionally does not aggregate the records or infer that hysteresis occurred.

For detached runs, invoke the remote function directly with a newly generated UUID4
collection ID (the Volume artifact is the source of truth)::

    modal run --detach sim/experiments/modal_canonical_hysteresis_collection.py::remote_collect \
      --collection-id 4f0dce79-9d19-4cdf-bc35-508fa95a5521

Monitor it with ``modal app list`` (and ``modal app logs <app-id>``).  Download
its durable result after it completes with::

    modal volume get canonical-hysteresis-raw-collections \
      4f0dce79-9d19-4cdf-bc35-508fa95a5521.json hysteresis-raw.json

The normal local entrypoint accepts the same ``--collection-id`` and can write
an optional local copy only after reading and verifying that Volume artifact.
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable
import uuid

from sim.experiments.hysteresis_runner import (
    HysteresisRunner,
    experiment_metadata,
    run_hysteresis_schedule,
)
from sim.swarm_kernel import Config

DEFAULT_REPLICATES = 12
DEFAULT_STEPS_PER_GAMMA = 500
DEFAULT_SEED = 202503
DEFAULT_GAMMA_SCHEDULE = tuple(round(index / 10, 1) for index in range(11))
# Keep raw evidence separate from ephemeral containers and give downloaders a
# stable public name.
COLLECTION_VOLUME_NAME = "canonical-hysteresis-raw-collections"
COLLECTION_VOLUME_MOUNT_PATH = "/collections"
_UUID4_COLLECTION_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def validate_collection_id(collection_id: str) -> str:
    """Return a canonical UUID4 collection ID suitable for a unique artifact.

    Requiring a UUID4, rather than accepting a user-selected filename, prevents
    traversal and makes accidental artifact-name collisions impractical.
    """
    if not isinstance(collection_id, str) or not _UUID4_COLLECTION_ID.fullmatch(collection_id):
        raise ValueError("collection_id must be a canonical lowercase UUID4")
    # Retain an explicit UUID parse as a guard if this pattern is ever changed.
    parsed = uuid.UUID(collection_id)
    if parsed.version != 4:
        raise ValueError("collection_id must be a UUID4")
    return collection_id


def collection_volume_relative_path(collection_id: str) -> str:
    """Return the validated artifact path relative to the Volume root."""
    return f"{validate_collection_id(collection_id)}.json"


def collection_artifact_path(collection_id: str) -> str:
    """Return the absolute mounted-container path for a validated collection ID."""
    return f"{COLLECTION_VOLUME_MOUNT_PATH}/{collection_volume_relative_path(collection_id)}"


def serialize_collection(collection: dict[str, Any]) -> bytes:
    """Produce deterministic, JSON-safe bytes for persistence and checksums."""
    return (json.dumps(collection, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def collection_sha256(serialized_collection: bytes) -> str:
    """Return the SHA-256 checksum of serialized collection bytes."""
    return hashlib.sha256(serialized_collection).hexdigest()


def deserialize_collection(serialized_collection: bytes, expected_sha256: str | None = None) -> dict[str, Any]:
    """Verify and decode a persisted collection artifact."""
    checksum = collection_sha256(serialized_collection)
    if expected_sha256 is not None and checksum != expected_sha256:
        raise ValueError("persisted collection checksum does not match remote metadata")
    decoded = json.loads(serialized_collection.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("persisted collection must be a JSON object")
    return decoded


def parse_gamma_schedule(gammas: str | Iterable[float]) -> list[float]:
    """Normalize a comma-delimited string or numeric iterable to a schedule."""
    try:
        values = (
            [part.strip() for part in gammas.split(",") if part.strip()]
            if isinstance(gammas, str)
            else list(gammas)
        )
        schedule = [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise ValueError("gammas must be a comma-separated string or numeric iterable") from exc
    if not schedule:
        raise ValueError("gammas must contain at least one value")
    return schedule


def canonical_kernel_sha256() -> str:
    """Return the digest of the repository's canonical kernel source."""
    source = Path(__file__).resolve().parents[1] / "swarm_kernel.py"
    return hashlib.sha256(source.read_bytes()).hexdigest()


def collect_canonical_hysteresis(
    *,
    replicates: int = DEFAULT_REPLICATES,
    steps_per_gamma: int = DEFAULT_STEPS_PER_GAMMA,
    seed: int = DEFAULT_SEED,
    gammas: str | Iterable[float] = DEFAULT_GAMMA_SCHEDULE,
    config: Config | None = None,
) -> dict[str, Any]:
    """Return JSON-safe raw records from the canonical schedule runner.

    The optional ``config`` exists for local preflight tests; the default is
    the repository ``Config``.  Records are deliberately unaggregated, so this
    is evidence collection rather than a hysteresis inference procedure.
    """
    schedule = parse_gamma_schedule(gammas)
    if replicates < 1:
        raise ValueError("replicates must be at least one")
    if steps_per_gamma < 0:
        raise ValueError("steps_per_gamma must be non-negative")

    resolved_config = copy.deepcopy(config) if config is not None else Config()
    resolved_config.seed = seed
    resolved_config.coercion = schedule[0]
    # This is the canonical state-carrying implementation; no kernel or
    # schedule loop is reproduced in this Modal launcher.
    records = run_hysteresis_schedule(
        schedule,
        replicates=replicates,
        steps_per_gamma=steps_per_gamma,
        seed=seed,
        config=resolved_config,
    )
    metadata = experiment_metadata(
        resolved_config, schedule, steps_per_gamma, replicates, seed,
    )
    metadata.update({
        "collection_purpose": (
            "Raw schedule evidence collection only; these records do not infer hysteresis."
        ),
        "provenance": {
            "canonical_kernel_module": "sim.swarm_kernel.SwarmKernel",
            "canonical_kernel_sha256": canonical_kernel_sha256(),
            "canonical_runner_module": "sim.experiments.hysteresis_runner",
            "canonical_runner_callable": "run_hysteresis_schedule",
            "schedule_runner": "HysteresisRunner",
        },
    })
    collection: dict[str, Any] = {
        "config": asdict(resolved_config),
        "metadata": metadata,
        "records": records,
    }
    # Fail locally instead of returning a result that Modal cannot serialize or
    # a JSON artifact that a downstream reader cannot consume.
    serialize_collection(collection)
    return collection


def write_collection(output: str | Path, collection: dict[str, Any]) -> Path:
    """Exclusively write a collection artifact; never replace prior evidence."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as destination:
        destination.write(serialize_collection(collection))
    return path


try:  # Importing the testable local core must not require Modal.
    import modal
except ImportError:  # pragma: no cover - depends on an intentionally lean environment
    modal = None


if modal is not None:
    app = modal.App("canonical-hysteresis-raw-collection")
    collection_volume = modal.Volume.from_name(COLLECTION_VOLUME_NAME, create_if_missing=True)
    # Upload the repository package, including the canonical runner and kernel.
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
        steps_per_gamma: int = DEFAULT_STEPS_PER_GAMMA,
        seed: int = DEFAULT_SEED,
        # Modal CLI exposes remote function arguments, so keep this a
        # CLI-serializable comma-separated string rather than a union type.
        gammas: str = ",".join(str(value) for value in DEFAULT_GAMMA_SCHEDULE),
    ) -> dict[str, Any]:
        """Persist raw evidence in the named Volume and return artifact metadata."""
        from sim.experiments.hysteresis_runner import HysteresisRunner as RemoteHysteresisRunner
        from sim.experiments.hysteresis_runner import run_hysteresis_schedule as remote_schedule
        from sim.experiments.modal_canonical_hysteresis_collection import (
            collection_artifact_path,
            collection_sha256,
            collect_canonical_hysteresis,
            serialize_collection,
        )

        # Keep the remote boundary auditable: this function uses the uploaded
        # repository implementation rather than an inline simulation kernel.
        assert RemoteHysteresisRunner is not None and remote_schedule is not None
        collection = collect_canonical_hysteresis(
            replicates=replicates,
            steps_per_gamma=steps_per_gamma,
            seed=seed,
            gammas=gammas,
        )
        artifact_path = collection_artifact_path(collection_id)
        serialized = serialize_collection(collection)
        # Exclusive creation protects existing evidence even if an ID is reused.
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
        steps_per_gamma: int = DEFAULT_STEPS_PER_GAMMA,
        seed: int = DEFAULT_SEED,
        gammas: str = ",".join(str(value) for value in DEFAULT_GAMMA_SCHEDULE),
    ) -> None:
        """Write a local copy only after reading the committed Volume artifact."""
        artifact = remote_collect.remote(collection_id, replicates, steps_per_gamma, seed, gammas)
        # The returned object is metadata, never an alternative result source.
        serialized = b"".join(collection_volume.read_file(artifact["volume_relative_path"]))
        collection = deserialize_collection(serialized, artifact["checksum"])
        write_collection(output, collection)
