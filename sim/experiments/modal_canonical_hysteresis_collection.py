"""Modal launcher for raw canonical hysteresis-schedule collections.

This launcher collects state-carrying schedule measurements as evidence.  It
intentionally does not aggregate the records or infer that hysteresis occurred.

Run a detached collection with::

    modal run --detach sim/experiments/modal_canonical_hysteresis_collection.py \
      --output hysteresis-raw.json
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

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
    json.dumps(collection, allow_nan=False)
    return collection


def write_collection(output: str | Path, collection: dict[str, Any]) -> Path:
    """Exclusively write a collection artifact; never replace prior evidence."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as destination:
        json.dump(collection, destination, indent=2, sort_keys=True, allow_nan=False)
    return path


try:  # Importing the testable local core must not require Modal.
    import modal
except ImportError:  # pragma: no cover - depends on an intentionally lean environment
    modal = None


if modal is not None:
    app = modal.App("canonical-hysteresis-raw-collection")
    # Upload the repository package, including the canonical runner and kernel.
    image = modal.Image.debian_slim(python_version="3.11").add_local_dir(
        local_path=str(Path(__file__).resolve().parents[1]), remote_path="/root/sim",
    )

    @app.function(image=image, timeout=3600, cpu=1)
    def remote_collect(
        replicates: int = DEFAULT_REPLICATES,
        steps_per_gamma: int = DEFAULT_STEPS_PER_GAMMA,
        seed: int = DEFAULT_SEED,
        gammas: str | list[float] = list(DEFAULT_GAMMA_SCHEDULE),
    ) -> dict[str, Any]:
        """Run the uploaded canonical runner remotely and return raw evidence."""
        from sim.experiments.hysteresis_runner import HysteresisRunner as RemoteHysteresisRunner
        from sim.experiments.hysteresis_runner import run_hysteresis_schedule as remote_schedule
        from sim.experiments.modal_canonical_hysteresis_collection import collect_canonical_hysteresis

        # Keep the remote boundary auditable: this function uses the uploaded
        # repository implementation rather than an inline simulation kernel.
        assert RemoteHysteresisRunner is not None and remote_schedule is not None
        return collect_canonical_hysteresis(
            replicates=replicates,
            steps_per_gamma=steps_per_gamma,
            seed=seed,
            gammas=gammas,
        )

    @app.local_entrypoint()
    def main(
        output: str,
        replicates: int = DEFAULT_REPLICATES,
        steps_per_gamma: int = DEFAULT_STEPS_PER_GAMMA,
        seed: int = DEFAULT_SEED,
        gammas: str = ",".join(str(value) for value in DEFAULT_GAMMA_SCHEDULE),
    ) -> None:
        """Fetch remote raw evidence and write the requested new JSON artifact."""
        collection = remote_collect.remote(replicates, steps_per_gamma, seed, gammas)
        write_collection(output, collection)
