"""Deterministic descriptive analysis of raw canonical coercion ablations.

The paired contrasts in this module describe simulation output only.  They are
not estimates of causal effects, and no causal inference is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import fmean
from typing import Any, Iterable

DEFAULT_BOOTSTRAP_SEED = 202503
DEFAULT_BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_CONFIDENCE_LEVEL = 0.95
CONDITIONS = ("null_gamma", "contact_homophily")
CLUSTER_METRICS = ("dominance", "effective_cluster_count", "entropy")


class CollectionValidationError(ValueError):
    """Raised when raw records do not form the declared matched pairs."""

    def __init__(self, failures: list[str]):
        self.failures = failures
        super().__init__("invalid raw coercion-ablation collection: " + "; ".join(failures))


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _summary(values: Iterable[float]) -> dict[str, float | int]:
    data = list(values)
    mean = fmean(data)
    return {
        "count": len(data),
        "mean": mean,
        "standard_deviation": (
            math.sqrt(sum((value - mean) ** 2 for value in data) / (len(data) - 1))
            if len(data) > 1 else 0.0
        ),
        "minimum": min(data),
        "maximum": max(data),
    }


def _bootstrap_mean_ci(
    values: list[float], *, seed: int, metric: str, gamma: float,
    resamples: int, confidence_level: float,
) -> dict[str, float]:
    # Deriving a stream per cell means adding a newly available kernel metric
    # cannot silently alter intervals for existing metrics.
    stream = hashlib.sha256(f"{seed}|{metric}|{gamma!r}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(stream, "big"))
    count = len(values)
    means = [fmean(values[rng.randrange(count)] for _ in range(count)) for _ in range(resamples)]
    tail = (1.0 - confidence_level) / 2.0
    return {"lower": _percentile(means, tail), "upper": _percentile(means, 1.0 - tail)}


def validate_raw_collection(collection: Any) -> dict[str, Any]:
    """Require one exact, fingerprint-matched condition pair per declared cell."""
    if not isinstance(collection, dict):
        raise CollectionValidationError(["top-level collection must be an object"])
    failures: list[str] = []
    warnings: list[str] = []
    metadata = collection.get("metadata")
    records = collection.get("records")
    if not isinstance(metadata, dict):
        failures.append("metadata must be an object")
    if not isinstance(records, list):
        failures.append("records must be an array")
    if failures:
        raise CollectionValidationError(failures)

    schedule_object = metadata.get("schedule")
    schedule = schedule_object.get("requested_gammas") if isinstance(schedule_object, dict) else None
    if not isinstance(schedule, list) or not schedule:
        failures.append("metadata.schedule.requested_gammas must be a non-empty array")
        gammas: list[float] = []
    elif not all(_finite_number(value) for value in schedule):
        failures.append("metadata.schedule.requested_gammas must contain finite numbers")
        gammas = []
    else:
        gammas = [float(value) for value in schedule]
        if len(set(gammas)) != len(gammas):
            failures.append("metadata.schedule.requested_gammas must not contain duplicates")
    declared_count = metadata.get("replicate_count")
    if not isinstance(declared_count, int) or isinstance(declared_count, bool) or declared_count < 1:
        failures.append("metadata.replicate_count must be a positive integer")
    declared_conditions = metadata.get("conditions")
    if declared_conditions != list(CONDITIONS):
        failures.append(f"metadata.conditions must be exactly {list(CONDITIONS)!r}")

    pairs: dict[tuple[int, float], dict[str, dict[str, Any]]] = {}
    kernel_key_sets: list[set[str]] = []
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{prefix} must be an object")
            continue
        replicate = record.get("replicate")
        gamma = record.get("requested_gamma")
        condition = record.get("condition")
        seed = record.get("seed")
        fingerprint = record.get("initial_state_fingerprint")
        if not isinstance(replicate, int) or isinstance(replicate, bool):
            failures.append(f"{prefix}.replicate must be an integer")
            continue
        if not _finite_number(gamma):
            failures.append(f"{prefix}.requested_gamma must be a finite number")
            continue
        gamma = float(gamma)
        if gammas and gamma not in gammas:
            failures.append(f"{prefix}.requested_gamma is not in the requested schedule")
            continue
        if condition not in CONDITIONS:
            failures.append(f"{prefix}.condition must be one of {CONDITIONS!r}")
            continue
        if not isinstance(seed, int) or isinstance(seed, bool):
            failures.append(f"{prefix}.seed must be an integer")
        if not isinstance(fingerprint, str) or not fingerprint:
            failures.append(f"{prefix}.initial_state_fingerprint must be a non-empty string")

        effective_gamma = record.get("effective_gamma")
        expected_effective = 0.0 if condition == "null_gamma" else gamma
        if not _finite_number(effective_gamma) or float(effective_gamma) != expected_effective:
            failures.append(f"{prefix}.effective_gamma is inconsistent with its condition")

        raw_metrics = record.get("raw_metrics")
        clusters = raw_metrics.get("clusters") if isinstance(raw_metrics, dict) else None
        kernel = raw_metrics.get("kernel") if isinstance(raw_metrics, dict) else None
        if not isinstance(clusters, dict):
            failures.append(f"{prefix}.raw_metrics.clusters must be an object")
        else:
            for name in CLUSTER_METRICS:
                if not _finite_number(clusters.get(name)):
                    failures.append(f"{prefix}.raw_metrics.clusters.{name} must be a finite number")
        if not isinstance(kernel, dict):
            failures.append(f"{prefix}.raw_metrics.kernel must be an object")
        else:
            scalar_keys = {name for name, value in kernel.items() if _finite_number(value)}
            kernel_key_sets.append(scalar_keys)
            for name, value in kernel.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(float(value)):
                    failures.append(f"{prefix}.raw_metrics.kernel.{name} must be finite")

        key = (replicate, gamma)
        branch = pairs.setdefault(key, {})
        if condition in branch:
            failures.append(f"duplicate {condition} record for replicate {replicate}, requested gamma {gamma}")
        else:
            branch[condition] = record

    if isinstance(declared_count, int) and not isinstance(declared_count, bool) and declared_count >= 1:
        observed_replicates = {replicate for replicate, _ in pairs}
        expected_replicates = set(range(declared_count))
        if observed_replicates != expected_replicates:
            failures.append(
                f"replicate identifiers must be exactly {sorted(expected_replicates)}, got {sorted(observed_replicates)}"
            )
        expected_cells = {(replicate, gamma) for replicate in expected_replicates for gamma in gammas}
        if set(pairs) != expected_cells:
            missing = sorted(expected_cells - set(pairs))
            extra = sorted(set(pairs) - expected_cells)
            failures.append(f"records do not cover every replicate/requested gamma (missing={missing}, extra={extra})")

    for (replicate, gamma), pair in pairs.items():
        if set(pair) != set(CONDITIONS):
            failures.append(
                f"replicate {replicate}, requested gamma {gamma} must have exactly one record for each condition"
            )
            continue
        null = pair["null_gamma"]
        contact = pair["contact_homophily"]
        if null.get("seed") != contact.get("seed"):
            failures.append(f"replicate {replicate}, requested gamma {gamma} has mismatched seeds")
        if null.get("initial_state_fingerprint") != contact.get("initial_state_fingerprint"):
            failures.append(f"replicate {replicate}, requested gamma {gamma} has mismatched initial fingerprints")

    kernel_metrics: list[str] = []
    if kernel_key_sets:
        kernel_metrics = sorted(set.intersection(*kernel_key_sets))
        union = set.union(*kernel_key_sets)
        excluded = sorted(union - set(kernel_metrics))
        if excluded:
            warnings.append(
                "Kernel metrics not finite and available in every record were excluded: " + ", ".join(excluded)
            )
    if failures:
        raise CollectionValidationError(failures)
    return {"gammas": gammas, "pairs": pairs, "kernel_metrics": kernel_metrics, "warnings": warnings}


def analyze_collection(
    collection: Any, *, bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> dict[str, Any]:
    """Calculate descriptive contact-minus-null paired differences."""
    if not isinstance(bootstrap_seed, int) or isinstance(bootstrap_seed, bool):
        raise ValueError("bootstrap_seed must be an integer")
    if not isinstance(bootstrap_resamples, int) or isinstance(bootstrap_resamples, bool) or bootstrap_resamples < 1:
        raise ValueError("bootstrap_resamples must be a positive integer")
    if not _finite_number(confidence_level) or not 0.0 < float(confidence_level) < 1.0:
        raise ValueError("confidence_level must be finite and between zero and one")

    validated = validate_raw_collection(collection)
    gammas: list[float] = validated["gammas"]
    pairs = validated["pairs"]
    kernel_metrics: list[str] = validated["kernel_metrics"]
    metric_sources = {name: ("clusters", name) for name in CLUSTER_METRICS}
    metric_sources.update({f"kernel.{name}": ("kernel", name) for name in kernel_metrics})

    per_pair: list[dict[str, Any]] = []
    differences: dict[float, dict[str, list[float]]] = {
        gamma: {name: [] for name in metric_sources} for gamma in gammas
    }
    replicate_count = collection["metadata"]["replicate_count"]
    for gamma in gammas:
        for replicate in range(replicate_count):
            pair = pairs[(replicate, gamma)]
            null = pair["null_gamma"]
            contact = pair["contact_homophily"]
            metric_values: dict[str, dict[str, float]] = {}
            for output_name, (section, source_name) in metric_sources.items():
                null_value = float(null["raw_metrics"][section][source_name])
                contact_value = float(contact["raw_metrics"][section][source_name])
                difference = contact_value - null_value
                differences[gamma][output_name].append(difference)
                metric_values[output_name] = {
                    "null_gamma": null_value,
                    "contact_homophily": contact_value,
                    "contact_minus_null": difference,
                }
            per_pair.append({
                "replicate": replicate,
                "seed": null["seed"],
                "requested_gamma": gamma,
                "initial_state_fingerprint": null["initial_state_fingerprint"],
                "metrics": metric_values,
            })

    by_gamma = []
    for gamma in gammas:
        reports = {}
        for name in metric_sources:
            values = differences[gamma][name]
            reports[name] = {
                "per_replicate_contact_minus_null": values,
                "descriptive_summary": _summary(values),
                "bootstrap_replicate_mean_confidence_interval": _bootstrap_mean_ci(
                    values, seed=bootstrap_seed, metric=name, gamma=gamma,
                    resamples=bootstrap_resamples, confidence_level=float(confidence_level),
                ),
            }
        by_gamma.append({"requested_gamma": gamma, "metrics": reports})

    warnings = list(validated["warnings"])
    if replicate_count == 1:
        warnings.append(
            "Only one replicate is available; bootstrap resampling cannot characterize between-replicate variation."
        )
    return {
        "analysis_type": "descriptive matched-pair coercion-ablation summaries",
        "validation": {
            "passed": True,
            "failures": [],
            "checks": [
                "exactly one null_gamma and one contact_homophily record per replicate/requested gamma",
                "paired seeds and initial_state_fingerprint values match",
                "required cluster metrics and included kernel metrics are finite",
            ],
        },
        "formulae": {
            "paired_difference": "contact_homophily value - null_gamma value for the same replicate and requested gamma",
            "mean_difference": "arithmetic mean of paired contact-minus-null differences across replicates at one requested gamma",
            "standard_deviation": "sample standard deviation of paired differences (zero when only one replicate is present)",
        },
        "bootstrap": {
            "seed": bootstrap_seed,
            "resamples": bootstrap_resamples,
            "confidence_level": float(confidence_level),
            "method": "fixed-seed percentile bootstrap of replicate mean paired differences, sampling replicates with replacement",
            "percentile_interpolation": "linear interpolation at equal-tailed percentiles",
        },
        "metrics": list(metric_sources),
        "per_pair": per_pair,
        "by_requested_gamma": by_gamma,
        "warnings": warnings,
        "interpretation": (
            "This report is descriptive only. The condition labels do not identify a causal effect; "
            "these summaries support no causal inference and no causal inference is made."
        ),
    }


def serialize_report(report: dict[str, Any]) -> str:
    """Return deterministic strict JSON text."""
    return json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"


def write_report(output: str | Path, report: dict[str, Any]) -> Path:
    """Write a report exclusively, refusing to replace an existing artifact."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as destination:
        destination.write(serialize_report(report))
    return path


def _reject_nonfinite_json(token: str) -> None:
    raise ValueError(f"input is not strict JSON: {token}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Describe matched raw canonical coercion-ablation records.")
    parser.add_argument("--input", required=True, type=Path, help="raw canonical collection JSON")
    parser.add_argument("--output", required=True, type=Path, help="new descriptive report JSON")
    parser.add_argument("--bootstrap-seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    parser.add_argument("--bootstrap-resamples", type=int, default=DEFAULT_BOOTSTRAP_RESAMPLES)
    parser.add_argument("--confidence-level", type=float, default=DEFAULT_CONFIDENCE_LEVEL)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {args.output}")
    if args.input.resolve() == args.output.resolve():
        raise ValueError("input and output paths must be different")
    with args.input.open(encoding="utf-8") as source:
        collection = json.load(source, parse_constant=_reject_nonfinite_json)
    report = analyze_collection(
        collection, bootstrap_seed=args.bootstrap_seed,
        bootstrap_resamples=args.bootstrap_resamples,
        confidence_level=args.confidence_level,
    )
    write_report(args.output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
