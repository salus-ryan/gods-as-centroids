from __future__ import annotations

import argparse
from dataclasses import asdict, fields
import json
from pathlib import Path
import platform
import subprocess
import sys

from swarm_kernel import Config, SwarmKernel, Callbacks


class PrintCB(Callbacks):
    def on_step(self, t: int, k: SwarmKernel):
        if t % 500 == 0:
            snap = k.snapshot()
            m = snap["metrics"]
            print(
                f"t={snap['t']:6d} gen={snap['gen']} | "
                f"zipf={m['zipf_slope']:+.2f} heapsK={m['heaps_k']:.3f} "
                f"H={m['cond_entropy']:.2f} topo={m['topo_similarity']:+.2f} "
                f"churn={m['churn']:.2f} | top={snap['top_forms'][:5]}"
            )

    def on_generation(self, gen: int, k: SwarmKernel):
        print(f"-- generation {gen} --")


def load_config(path: Path | None) -> Config:
    """Load a plain JSON object whose keys are exactly Config field names."""
    if path is None:
        return Config()
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Config JSON must be a plain object containing Config fields")
    if "parameters" in data and ("source" in data or "deity_priors" in data):
        raise ValueError(
            "Corpus-calibrated wrapper configs are not accepted here; convert them "
            "explicitly to a plain Config JSON object before running."
        )

    config_keys = {field.name for field in fields(Config)}
    unknown_keys = sorted(set(data) - config_keys)
    if unknown_keys:
        raise ValueError(f"Unknown Config key(s): {', '.join(unknown_keys)}")
    return Config(**data)


def git_revision() -> str | None:
    """Return the current revision when this checkout has git metadata."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def write_provenance(path: Path, cfg: Config, steps: int) -> None:
    """Create the run's write-once record of its resolved execution inputs."""
    provenance = {
        "config": asdict(cfg),
        "requested_steps": steps,
        "seed": cfg.seed,
        "git_revision": git_revision(),
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }
    # Exclusive creation prevents a provenance record from being overwritten.
    with path.open("x") as f:
        json.dump(provenance, f, indent=2, sort_keys=True)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=None, help="Path to JSON config")
    ap.add_argument("--steps", type=int, default=5000, help="Number of steps to run")
    ap.add_argument("--outdir", type=Path, default=Path("sim/runs"), help="Base output directory for runs")
    ap.add_argument("--label", type=str, default=None, help="Optional run label for directory name")
    args = ap.parse_args()

    cfg = load_config(args.config)
    kern = SwarmKernel(cfg)
    # Prepare output directory
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = f"_{args.label}" if args.label else ""
    run_dir = args.outdir / f"{ts}{label}"
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = run_dir / "metrics.jsonl"
    snapshot_path = run_dir / "snapshot.json"
    provenance_path = run_dir / "provenance.json"
    write_provenance(provenance_path, cfg, args.steps)

    class LogCB(PrintCB):
        def on_step(self, t: int, k: SwarmKernel):
            super().on_step(t, k)
            if t % 25 == 0:
                snap = k.snapshot()
                rec = {
                    "t": snap["t"],
                    "gen": snap["gen"],
                    **{f"m_{k}": v for k, v in snap["metrics"].items()},
                }
                with metrics_path.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
        def on_generation(self, gen: int, k: SwarmKernel):
            super().on_generation(gen, k)

    kern.run(steps=args.steps, callbacks=LogCB())
    with snapshot_path.open("w") as f:
        json.dump(kern.snapshot(), f, indent=2)
    print(json.dumps({"run_dir": str(run_dir)}, indent=2))


if __name__ == "__main__":
    main()
