"""Collect raw matched-state coercion ablations without aggregation or inference.

The two conditions are deliberately initialized with ``coercion=0`` before a
condition is applied.  This makes the recorded initial-state fingerprint an
exact matched-state check for every (seed, requested gamma) pair.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

try:  # Supports module invocation and legacy use with sim on sys.path.
    from ..swarm_kernel import Config, SwarmKernel
    from .hysteresis_runner import experiment_metadata, measure_clusters, state_fingerprint
except ImportError:  # pragma: no cover - exercised only when sim is on sys.path
    from swarm_kernel import Config, SwarmKernel
    from hysteresis_runner import experiment_metadata, measure_clusters, state_fingerprint


NULL_GAMMA = "null_gamma"
CONTACT_HOMOPHILY = "contact_homophily"
CONDITIONS = (NULL_GAMMA, CONTACT_HOMOPHILY)


class CoercionAblationCollector:
    """Run each labeled condition from an independently recreated baseline."""

    def __init__(self, config: Config, gammas: Iterable[float], steps: int):
        self.config = copy.deepcopy(config)
        self.gammas = tuple(float(gamma) for gamma in gammas)
        self.steps = steps
        if not self.gammas:
            raise ValueError("gammas must contain at least one value")
        if any(not math.isfinite(gamma) or gamma < 0.0 for gamma in self.gammas):
            raise ValueError("gammas must be finite and non-negative")
        if steps < 0:
            raise ValueError("steps must be non-negative")

    def _run_condition(
        self, seed: int, replicate: int, requested_gamma: float, condition: str,
    ) -> dict[str, object]:
        # Coercion is assigned only after fingerprinting this baseline.  It does
        # not affect kernel initialization, and this explicit order makes the
        # paired initial state independently verifiable in raw output.
        cfg = copy.deepcopy(self.config)
        cfg.seed = seed
        cfg.coercion = 0.0
        kernel = SwarmKernel(cfg)
        initial_state_fingerprint = state_fingerprint(kernel)

        if condition == NULL_GAMMA:
            effective_gamma = 0.0
        elif condition == CONTACT_HOMOPHILY:
            effective_gamma = requested_gamma
        else:  # Keep condition labels closed and serializable.
            raise ValueError(f"unknown condition: {condition!r}")
        kernel.cfg.coercion = effective_gamma
        kernel.run(self.steps)

        # ``measure_clusters`` uses the kernel's fixed cluster configuration;
        # coercion is never supplied as a measurement threshold or setting.
        raw_metrics = {
            "clusters": measure_clusters(kernel),
            "kernel": asdict(kernel.metrics),
            "time": kernel.t,
        }
        return {
            "condition": condition,
            "requested_gamma": requested_gamma,
            "effective_gamma": effective_gamma,
            "seed": seed,
            "replicate": replicate,
            "initial_state_fingerprint": initial_state_fingerprint,
            "state_fingerprint": state_fingerprint(kernel),
            "raw_metrics": raw_metrics,
        }

    def run_replicate(self, seed: int, replicate: int = 0) -> list[dict[str, object]]:
        """Return raw records for all gammas and both explicitly labeled conditions."""
        return [
            self._run_condition(seed, replicate, gamma, condition)
            for gamma in self.gammas
            for condition in CONDITIONS
        ]


def collect_coercion_ablation(
    gammas: Iterable[float],
    *,
    replicates: int = 1,
    seed: int = 7,
    steps: int = 100,
    config: Optional[Config] = None,
) -> list[dict[str, object]]:
    """Collect unaggregated paired-condition records for independent replicates."""
    if replicates < 1:
        raise ValueError("replicates must be at least one")
    collector = CoercionAblationCollector(config or Config(), gammas, steps)
    return [
        record
        for replicate in range(replicates)
        for record in collector.run_replicate(seed + replicate, replicate)
    ]


def _parse_gammas(value: str) -> list[float]:
    try:
        return [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("gammas must be comma-separated numbers") from exc


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Write raw matched-state coercion ablation records as JSON.")
    parser.add_argument("--output", required=True, type=Path, help="JSON output path (must not already exist)")
    parser.add_argument("--gammas", default="0,0.25,0.5,0.75,1", type=_parse_gammas)
    parser.add_argument("--replicates", default=1, type=int)
    parser.add_argument("--seed", default=7, type=int)
    parser.add_argument("--steps", default=100, type=int)
    parser.add_argument("--agents", default=64, type=int)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {args.output}")
    if args.replicates < 1:
        parser.error("--replicates must be at least one")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # The collection baseline has no coercion. Conditions set it per record.
    config = Config(N=args.agents, seed=args.seed, coercion=0.0)
    collector = CoercionAblationCollector(config, args.gammas, args.steps)
    records = [
        record
        for replicate in range(args.replicates)
        for record in collector.run_replicate(args.seed + replicate, replicate)
    ]
    metadata = experiment_metadata(config, collector.gammas, args.steps, args.replicates, args.seed)
    metadata.update({
        "schedule": {"requested_gammas": list(collector.gammas), "steps": args.steps},
        "conditions": list(CONDITIONS),
        "measurement": {
            "cluster_method": "fixed kernel cluster configuration",
            "gamma_independent": True,
        },
    })
    with args.output.open("x", encoding="utf-8") as output:
        json.dump({"config": asdict(config), "metadata": metadata, "records": records}, output, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
