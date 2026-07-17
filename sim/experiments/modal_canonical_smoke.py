"""Tiny Modal smoke test that executes the repository's canonical kernel.

Run locally without Modal: ``python -m sim.experiments.modal_canonical_smoke``.
Run remotely: ``modal run sim/experiments/modal_canonical_smoke.py``.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable, Dict, Tuple

from sim.swarm_kernel import AXES, Config, SwarmKernel


DEFAULT_SEED = 202503
SMOKE_STEPS = 16
# This is deliberately a single, small fixed configuration, not a sweep.
SMOKE_CONFIG = {
    "N": 8,
    "steps_per_generation": 10_000,
    "seed": DEFAULT_SEED,
    "social_network": "small_world",
    "social_k": 2,
    "social_p": 0.1,
    "cluster_update_freq": 4,
    "mutation_rate": 0.03,
    "form_mutation_rate": 0.02,
    "prophet_rate": 0.0,
    "fission_min_cluster_size": 99,
}


def canonical_kernel_fingerprint() -> str:
    """Return the SHA-256 of the canonical SwarmKernel implementation."""
    source = Path(__file__).resolve().parents[1] / "swarm_kernel.py"
    return hashlib.sha256(source.read_bytes()).hexdigest()


def _terminal_snapshot(kernel: SwarmKernel) -> Dict[str, Any]:
    """Build an ordered, JSON-safe terminal state snapshot for replay checks."""
    return {
        "t": kernel.t,
        "gen": kernel.gen,
        "metrics": asdict(kernel.metrics),
        "agents": [
            {
                "id": agent.id,
                "belief": [agent.belief[axis] for axis in AXES],
                "prestige": agent.w,
                "associations": [
                    [form, [vector[axis] for axis in AXES]]
                    for form, vector in sorted(agent.assoc.items())
                ],
                "frequencies": sorted(agent.freq.items()),
                "channels": list(agent.sensory_channels),
                "cluster_label": agent.cluster_label,
            }
            for agent in sorted(kernel.agents, key=lambda agent: agent.id)
        ],
        "social_graph": [
            [agent_id, sorted(neighbors)]
            for agent_id, neighbors in sorted(kernel.social_graph.items())
        ],
        "clusters": [sorted(cluster) for cluster in kernel.clusters],
        "cluster_labels": sorted(kernel.cluster_labels.items()),
        "tokens": list(kernel.tokens),
        "types": sorted(kernel.types.items()),
        "bigrams": [[list(pair), count] for pair, count in sorted(kernel.bigrams.items())],
    }


def _snapshot_digest(snapshot: Dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_canonical_once(seed: int = DEFAULT_SEED) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the canonical ``SwarmKernel`` once and return JSON-safe evidence.

    This core deliberately has no Modal dependency so it can be unit tested
    and used as a local preflight check.
    """
    config_values = dict(SMOKE_CONFIG, seed=seed)
    kernel = SwarmKernel(Config(**config_values))
    kernel.run(SMOKE_STEPS)
    snapshot = _terminal_snapshot(kernel)
    return (
        {
            "seed": seed,
            "steps": SMOKE_STEPS,
            "terminal_state_sha256": _snapshot_digest(snapshot),
        },
        snapshot,
    )


def run_identical_seed_smoke(
    seed: int = DEFAULT_SEED,
    run_once: Callable[[int], Tuple[Dict[str, Any], Dict[str, Any]]] = run_canonical_once,
) -> Dict[str, Any]:
    """Execute two same-seed runs and raise if their deterministic snapshots differ."""
    first, first_snapshot = run_once(seed)
    second, second_snapshot = run_once(seed)
    identical = first_snapshot == second_snapshot
    result = {
        "smoke_test": "canonical-swarm-kernel-identical-seed",
        "seed": seed,
        "config": asdict(Config(**dict(SMOKE_CONFIG, seed=seed))),
        "provenance": {
            "canonical_kernel_module": "sim.swarm_kernel.SwarmKernel",
            "canonical_kernel_sha256": canonical_kernel_fingerprint(),
            "python_version": sys.version.split()[0],
        },
        "runs": [first, second],
        "identical": identical,
    }
    # Keep this assertion after forming the evidence so callers get a useful
    # failure when replay behavior regresses rather than a silent false result.
    if not identical:
        raise AssertionError("canonical SwarmKernel identical-seed smoke run diverged")
    json.dumps(result, allow_nan=False)  # assert the public result is JSON-safe
    return result


try:  # Local/unit-test imports must work when Modal is intentionally absent.
    import modal
except ImportError:  # pragma: no cover - exercised by environments without Modal
    modal = None


if modal is not None:
    app = modal.App("canonical-swarm-kernel-smoke")
    # Upload the actual repository sim package.  The remote function imports
    # sim.swarm_kernel; it does not carry an inline or copied mini-kernel.
    image = modal.Image.debian_slim(python_version="3.11").add_local_dir(
        local_path=str(Path(__file__).resolve().parents[1]), remote_path="/root/sim"
    )

    @app.function(image=image, timeout=300, cpu=1)
    def remote_smoke(seed: int = DEFAULT_SEED) -> Dict[str, Any]:
        # Explicit remote import makes the canonical implementation boundary
        # auditable in the Modal execution environment.
        from sim.swarm_kernel import SwarmKernel as RemoteCanonicalSwarmKernel
        from sim.experiments.modal_canonical_smoke import run_identical_seed_smoke

        assert RemoteCanonicalSwarmKernel is not None
        return run_identical_seed_smoke(seed)

    @app.local_entrypoint()
    def main(seed: int = DEFAULT_SEED) -> None:
        print(json.dumps(remote_smoke.remote(seed), sort_keys=True))


if __name__ == "__main__" and modal is None:
    print(json.dumps(run_identical_seed_smoke(), sort_keys=True))
