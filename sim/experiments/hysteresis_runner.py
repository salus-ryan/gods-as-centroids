"""Raw state-carrying gamma-schedule experiment runner.

This module records the two directions of a schedule; it does not infer a
transition or make a claim about the relationship between their measurements.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

try:  # Supports both ``python -m sim.experiments...`` and legacy sim-path use.
    from ..swarm_kernel import Config, SwarmKernel
except ImportError:  # pragma: no cover - exercised only when sim is on sys.path
    from swarm_kernel import Config, SwarmKernel


def state_fingerprint(kernel: SwarmKernel) -> str:
    """Return an identifier for the complete pickled kernel state.

    The identifier includes RNG state, configuration, and all kernel-owned
    state.  It is intended for same-code-run continuity checks, not as a
    portable serialization format.
    """
    payload = pickle.dumps(kernel, protocol=pickle.HIGHEST_PROTOCOL)
    return hashlib.sha256(payload).hexdigest()


def measure_clusters(kernel: SwarmKernel) -> dict[str, float | int]:
    """Measure cluster membership from the current canonical kernel state."""
    kernel._update_clusters()
    sizes = [len(cluster) for cluster in kernel.clusters]
    population = len(kernel.agents)
    if not sizes or population == 0:
        return {"dominance": 0.0, "effective_cluster_count": 0.0, "entropy": 0.0}

    probabilities = [size / population for size in sizes if size]
    entropy = -sum(probability * math.log(probability) for probability in probabilities)
    # exp(H) is the entropy-effective number of occupied clusters.
    return {
        "dominance": max(probabilities),
        "effective_cluster_count": math.exp(entropy),
        "entropy": entropy,
    }


class HysteresisRunner:
    """Execute an ascending and descending schedule on one kernel per replicate."""

    def __init__(self, config: Config, gammas: Iterable[float], steps_per_gamma: int):
        self.config = copy.deepcopy(config)
        self.gammas = tuple(float(gamma) for gamma in gammas)
        self.steps_per_gamma = steps_per_gamma
        if not self.gammas:
            raise ValueError("gammas must contain at least one value")
        if self.gammas != tuple(sorted(self.gammas)):
            raise ValueError("gammas must be in ascending order")
        if steps_per_gamma < 0:
            raise ValueError("steps_per_gamma must be non-negative")

    def run_replicate(self, seed: int, replicate: int = 0) -> list[dict[str, object]]:
        """Run both branches, retaining the single initialized kernel state."""
        cfg = copy.deepcopy(self.config)
        cfg.seed = seed
        cfg.coercion = self.gammas[0]  # Initialization occurs at the low endpoint.
        kernel = SwarmKernel(cfg)
        records: list[dict[str, object]] = []

        for direction, schedule in (("ascending", self.gammas), ("descending", tuple(reversed(self.gammas)))):
            for gamma in schedule:
                starting_state_fingerprint = state_fingerprint(kernel)
                kernel.cfg.coercion = gamma
                kernel.run(self.steps_per_gamma)
                measurements = measure_clusters(kernel)
                records.append({
                    "replicate": replicate,
                    "direction": direction,
                    "seed": seed,
                    "gamma": gamma,
                    **measurements,
                    "starting_state_fingerprint": starting_state_fingerprint,
                    "state_fingerprint": state_fingerprint(kernel),
                })
        return records


def run_hysteresis_schedule(
    gammas: Iterable[float],
    *,
    replicates: int = 1,
    seed: int = 7,
    steps_per_gamma: int = 100,
    config: Optional[Config] = None,
) -> list[dict[str, object]]:
    """Run independent seeded replicates and return unaggregated records."""
    if replicates < 1:
        raise ValueError("replicates must be at least one")
    runner = HysteresisRunner(config or Config(), gammas, steps_per_gamma)
    return [
        record
        for replicate in range(replicates)
        for record in runner.run_replicate(seed + replicate, replicate)
    ]


def _parse_gammas(value: str) -> list[float]:
    try:
        return [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("gammas must be comma-separated numbers") from exc


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Write raw state-carrying gamma schedule records as JSON.")
    parser.add_argument("--output", required=True, type=Path, help="JSON output path")
    parser.add_argument("--gammas", default="0,0.25,0.5,0.75,1", type=_parse_gammas)
    parser.add_argument("--replicates", default=1, type=int)
    parser.add_argument("--seed", default=7, type=int)
    parser.add_argument("--steps-per-gamma", default=100, type=int)
    parser.add_argument("--agents", default=64, type=int)
    args = parser.parse_args(argv)

    config = Config(N=args.agents)
    records = run_hysteresis_schedule(
        args.gammas, replicates=args.replicates, seed=args.seed,
        steps_per_gamma=args.steps_per_gamma, config=config,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output:
        json.dump({"config": asdict(config), "records": records}, output, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
