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
import platform
import subprocess
import sys
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

    def run_replicate_with_terminal_state(
        self, seed: int, replicate: int = 0,
    ) -> tuple[list[dict[str, object]], SwarmKernel]:
        """Run one replicate and return its records and final canonical state.

        The returned kernel is the state after the descending branch.  It is
        deliberately returned only to support optional raw-state archival;
        measurements remain unaggregated records.
        """
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
        return records, kernel

    def run_replicate(self, seed: int, replicate: int = 0) -> list[dict[str, object]]:
        """Run both branches, retaining the single initialized kernel state."""
        records, _ = self.run_replicate_with_terminal_state(seed, replicate)
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


def _git_revision() -> Optional[str]:
    """Return the checked-out revision when this source is in a Git checkout."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def experiment_metadata(
    config: Config, gammas: Iterable[float], steps_per_gamma: int,
    replicates: int, seed: int,
) -> dict[str, object]:
    """Describe inputs and runtime needed to reproduce a raw collection run."""
    return {
        "gamma_schedule": [float(gamma) for gamma in gammas],
        "steps_per_gamma": steps_per_gamma,
        "replicate_count": replicates,
        "seed_scheme": {
            "base_seed": seed,
            "per_replicate": "base_seed + replicate_index",
        },
        "resolved_config": asdict(config),
        "git_revision": _git_revision(),
        "python": {
            "implementation": platform.python_implementation(),
            "version": sys.version,
        },
        "platform": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "system": platform.system(),
        },
    }


def _write_terminal_state(kernel: SwarmKernel, artifact_path: Path) -> str:
    """Write one local pickle artifact exclusively and return its SHA-256.

    Pickles are local reproducibility artifacts, not a stable or safe exchange
    format; only load artifacts produced by a trusted run of this code.
    """
    payload = pickle.dumps(kernel, protocol=pickle.HIGHEST_PROTOCOL)
    with artifact_path.open("xb") as artifact:
        artifact.write(payload)
    return hashlib.sha256(payload).hexdigest()


def _parse_gammas(value: str) -> list[float]:
    try:
        return [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("gammas must be comma-separated numbers") from exc


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Write raw state-carrying gamma schedule records as JSON.")
    parser.add_argument("--output", required=True, type=Path, help="JSON output path (must not already exist)")
    parser.add_argument("--gammas", default="0,0.25,0.5,0.75,1", type=_parse_gammas)
    parser.add_argument("--replicates", default=1, type=int)
    parser.add_argument("--seed", default=7, type=int)
    parser.add_argument("--steps-per-gamma", default=100, type=int)
    parser.add_argument("--agents", default=64, type=int)
    parser.add_argument(
        "--serialize-terminal-states", "--save-terminal-states",
        action="store_true", dest="serialize_terminal_states",
        help=("write one trusted-local pickle per replicate beside the JSON; "
              "each artifact is SHA-256 fingerprinted in the JSON"),
    )
    args = parser.parse_args(argv)
    if args.replicates < 1:
        parser.error("--replicates must be at least one")

    # Never replace a previous collection.  Artifact directories are likewise
    # created exclusively below, so concurrent/colliding invocations fail.
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Record the actual initialization settings; individual replicate seeds are
    # described by metadata.seed_scheme and applied by the runner.
    config = Config(N=args.agents, seed=args.seed, coercion=args.gammas[0])
    runner = HysteresisRunner(config, args.gammas, args.steps_per_gamma)
    records: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    artifact_dir: Optional[Path] = None
    if args.serialize_terminal_states:
        artifact_dir = args.output.parent / f"{args.output.stem}.terminal_states"
        artifact_dir.mkdir()  # exclusive: do not mix this run with an old one

    for replicate in range(args.replicates):
        replicate_seed = args.seed + replicate
        replicate_records, terminal_kernel = runner.run_replicate_with_terminal_state(
            replicate_seed, replicate,
        )
        records.extend(replicate_records)
        if artifact_dir is not None:
            artifact_path = artifact_dir / f"replicate-{replicate:04d}.pickle"
            checksum = _write_terminal_state(terminal_kernel, artifact_path)
            artifacts.append({
                "replicate": replicate,
                "seed": replicate_seed,
                "path": str(artifact_path.relative_to(args.output.parent)),
                "sha256": checksum,
                "format": "pickle",
            })

    metadata = experiment_metadata(
        config, runner.gammas, args.steps_per_gamma, args.replicates, args.seed,
    )
    metadata["terminal_state_artifacts"] = artifacts
    # ``config`` remains for compatibility with existing raw-output consumers;
    # metadata.resolved_config is the authoritative reproducibility record.
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(
            {"config": asdict(config), "metadata": metadata, "records": records},
            output, indent=2, sort_keys=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
