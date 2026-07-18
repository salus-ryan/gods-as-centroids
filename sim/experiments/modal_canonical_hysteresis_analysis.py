"""Deterministically summarize raw canonical schedule collections.

This module only describes the supplied measurements.  Its numerical summaries
and bootstrap intervals are not a result proof or an inference about a phase
transition or hysteresis.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
from statistics import fmean
from typing import Any, Iterable

DEFAULT_BOOTSTRAP_SEED = 202503
DEFAULT_BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_CONFIDENCE_LEVEL = 0.95


class CollectionValidationError(ValueError):
    """Raised when a raw collection cannot support paired calculations."""

    def __init__(self, failures: list[str]):
        self.failures = failures
        super().__init__("invalid raw collection: " + "; ".join(failures))


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _percentile(values: list[float], probability: float) -> float:
    """Linearly interpolated percentile for a non-empty sorted numeric sample."""
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
        "standard_deviation": math.sqrt(sum((value - mean) ** 2 for value in data) / (len(data) - 1)) if len(data) > 1 else 0.0,
        "minimum": min(data),
        "maximum": max(data),
    }


def _bootstrap_mean_ci(values: list[float], *, rng: random.Random, resamples: int, confidence_level: float) -> dict[str, float]:
    sample_size = len(values)
    means = [fmean(values[rng.randrange(sample_size)] for _ in range(sample_size)) for _ in range(resamples)]
    tail = (1.0 - confidence_level) / 2.0
    return {
        "lower": _percentile(means, tail),
        "upper": _percentile(means, 1.0 - tail),
    }


def validate_raw_collection(collection: Any) -> dict[str, Any]:
    """Validate analysis-required metadata and complete paired observations.

    The raw collector's full provenance is retained in the input, but this
    analyzer requires the metadata that identifies its schedule and replicate
    count plus one finite dominance observation per direction/gamma/replicate.
    """
    failures: list[str] = []
    if not isinstance(collection, dict):
        raise CollectionValidationError(["top-level collection must be an object"])
    metadata = collection.get("metadata")
    records = collection.get("records")
    if not isinstance(metadata, dict):
        failures.append("metadata must be an object")
    if not isinstance(records, list):
        failures.append("records must be an array")
    if failures:
        raise CollectionValidationError(failures)

    schedule = metadata.get("gamma_schedule")
    declared_count = metadata.get("replicate_count")
    if not isinstance(schedule, list) or not schedule:
        failures.append("metadata.gamma_schedule must be a non-empty array")
        schedule_values: list[float] = []
    elif not all(_finite_number(gamma) for gamma in schedule):
        failures.append("metadata.gamma_schedule must contain only finite numbers")
        schedule_values = []
    else:
        schedule_values = [float(gamma) for gamma in schedule]
        if any(right <= left for left, right in zip(schedule_values, schedule_values[1:])):
            failures.append("metadata.gamma_schedule must be strictly ascending without duplicates")
    if not isinstance(declared_count, int) or isinstance(declared_count, bool) or declared_count < 1:
        failures.append("metadata.replicate_count must be a positive integer")

    paired: dict[int, dict[str, dict[float, float]]] = {}
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{prefix} must be an object")
            continue
        replicate = record.get("replicate")
        direction = record.get("direction")
        gamma = record.get("gamma")
        dominance = record.get("dominance")
        if not isinstance(replicate, int) or isinstance(replicate, bool):
            failures.append(f"{prefix}.replicate must be an integer")
            continue
        if direction not in ("ascending", "descending"):
            failures.append(f"{prefix}.direction must be ascending or descending")
            continue
        if not _finite_number(gamma):
            failures.append(f"{prefix}.gamma must be a finite number")
            continue
        if not _finite_number(dominance):
            failures.append(f"{prefix}.dominance must be a finite number")
            continue
        gamma_value = float(gamma)
        if schedule_values and gamma_value not in schedule_values:
            failures.append(f"{prefix}.gamma is not in metadata.gamma_schedule")
            continue
        branch = paired.setdefault(replicate, {"ascending": {}, "descending": {}})[direction]
        if gamma_value in branch:
            failures.append(f"duplicate {direction} record for replicate {replicate}, gamma {gamma_value}")
        else:
            branch[gamma_value] = float(dominance)

    if isinstance(declared_count, int) and not isinstance(declared_count, bool) and declared_count >= 1:
        if len(paired) != declared_count:
            failures.append(f"metadata.replicate_count is {declared_count}, but records contain {len(paired)} replicates")
    expected = set(schedule_values)
    for replicate, branches in paired.items():
        for direction in ("ascending", "descending"):
            observed = set(branches[direction])
            if observed != expected:
                missing = sorted(expected - observed)
                extra = sorted(observed - expected)
                detail = []
                if missing:
                    detail.append(f"missing gammas {missing}")
                if extra:
                    detail.append(f"unexpected gammas {extra}")
                failures.append(f"replicate {replicate} {direction} records are not paired with schedule ({', '.join(detail)})")
    if failures:
        raise CollectionValidationError(failures)
    return {"schedule": schedule_values, "paired": paired}


def analyze_collection(
    collection: Any,
    *,
    bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> dict[str, Any]:
    """Return JSON-safe descriptive paired summaries for a valid raw collection."""
    if not isinstance(bootstrap_seed, int) or isinstance(bootstrap_seed, bool):
        raise ValueError("bootstrap_seed must be an integer")
    if not isinstance(bootstrap_resamples, int) or isinstance(bootstrap_resamples, bool) or bootstrap_resamples < 1:
        raise ValueError("bootstrap_resamples must be a positive integer")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between zero and one")
    validated = validate_raw_collection(collection)
    schedule: list[float] = validated["schedule"]
    paired: dict[int, dict[str, dict[float, float]]] = validated["paired"]
    replicate_values: list[dict[str, Any]] = []
    contrasts_by_gamma: dict[float, list[float]] = {gamma: [] for gamma in schedule}
    for replicate in sorted(paired):
        ascending = paired[replicate]["ascending"]
        descending = paired[replicate]["descending"]
        contrasts = []
        for gamma in schedule:
            contrast = descending[gamma] - ascending[gamma]
            contrasts_by_gamma[gamma].append(contrast)
            contrasts.append({"gamma": gamma, "ascending_dominance": ascending[gamma], "descending_dominance": descending[gamma], "descending_minus_ascending": contrast})
        # Both curves are integrated over ascending gamma, so their difference
        # is the signed trapezoidal loop area (descending minus ascending).
        area = sum(
            (schedule[index + 1] - schedule[index]) * (contrasts[index]["descending_minus_ascending"] + contrasts[index + 1]["descending_minus_ascending"]) / 2.0
            for index in range(len(schedule) - 1)
        )
        replicate_values.append({"replicate": replicate, "loop_area": area, "contrasts": contrasts})

    rng = random.Random(bootstrap_seed)
    areas = [entry["loop_area"] for entry in replicate_values]
    gamma_reports = []
    for gamma in schedule:
        values = contrasts_by_gamma[gamma]
        gamma_reports.append({
            "gamma": gamma,
            "per_replicate_descending_minus_ascending": values,
            "summary": _summary(values),
            "bootstrap_mean_confidence_interval": _bootstrap_mean_ci(values, rng=rng, resamples=bootstrap_resamples, confidence_level=confidence_level),
        })
    warnings = []
    if len(schedule) == 1:
        warnings.append("A one-point gamma schedule has a trapezoidal loop area of zero.")
    if len(replicate_values) == 1:
        warnings.append("Only one replicate is available; bootstrap resampling cannot characterize between-replicate variation.")
    return {
        "analysis_type": "descriptive paired dominance summaries",
        "validation": {"passed": True, "failures": [], "warnings": warnings},
        "formulae": {
            "loop_area": "signed integral over gamma of (descending dominance - ascending dominance), using the trapezoidal rule",
            "contrast": "descending dominance - ascending dominance at the same replicate and gamma",
        },
        "per_replicate": replicate_values,
        "loop_area_summary": _summary(areas),
        "loop_area_bootstrap_mean_confidence_interval": _bootstrap_mean_ci(areas, rng=rng, resamples=bootstrap_resamples, confidence_level=confidence_level),
        "contrasts_by_gamma": gamma_reports,
        "bootstrap": {"seed": bootstrap_seed, "resamples": bootstrap_resamples, "confidence_level": confidence_level, "method": "percentile bootstrap of replicate means, sampled with replacement"},
        "interpretation": "This report is descriptive only. It does not provide a result proof and does not infer a phase transition or hysteresis conclusion.",
    }


def write_report(output: str | Path, report: dict[str, Any]) -> Path:
    """Write one report exclusively, refusing to replace an existing file."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as destination:
        json.dump(report, destination, indent=2, sort_keys=True, allow_nan=False)
        destination.write("\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Describe paired dominance records from a raw canonical collection.")
    parser.add_argument("--input", required=True, type=Path, help="raw collection JSON")
    parser.add_argument("--output", required=True, type=Path, help="new report JSON path")
    parser.add_argument("--bootstrap-seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    parser.add_argument("--bootstrap-resamples", type=int, default=DEFAULT_BOOTSTRAP_RESAMPLES)
    parser.add_argument("--confidence-level", type=float, default=DEFAULT_CONFIDENCE_LEVEL)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {args.output}")
    with args.input.open(encoding="utf-8") as source:
        collection = json.load(source)
    report = analyze_collection(collection, bootstrap_seed=args.bootstrap_seed, bootstrap_resamples=args.bootstrap_resamples, confidence_level=args.confidence_level)
    write_report(args.output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
