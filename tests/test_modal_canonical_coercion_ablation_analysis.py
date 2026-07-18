import json

import pytest

from sim.experiments.modal_canonical_coercion_ablation_analysis import (
    CollectionValidationError,
    analyze_collection,
    main,
    serialize_report,
    validate_raw_collection,
)


def _collection():
    records = []
    for replicate in range(2):
        for gamma in (0.0, 0.5):
            baseline = 10.0 * replicate + gamma
            for condition, offset in (("null_gamma", 0.0), ("contact_homophily", 1.0 + replicate)):
                records.append({
                    "condition": condition,
                    "requested_gamma": gamma,
                    "effective_gamma": gamma if condition == "contact_homophily" else 0.0,
                    "replicate": replicate,
                    "seed": 100 + replicate,
                    "initial_state_fingerprint": f"initial-{replicate}-{gamma}",
                    "raw_metrics": {
                        "clusters": {
                            "dominance": baseline + offset,
                            "effective_cluster_count": baseline + 2.0 * offset,
                            "entropy": baseline - offset,
                        },
                        "kernel": {
                            "churn": baseline + 3.0 * offset,
                            "topo_similarity": baseline + 4.0 * offset,
                        },
                        "time": 5,
                    },
                })
    return {
        "metadata": {
            "replicate_count": 2,
            "conditions": ["null_gamma", "contact_homophily"],
            "schedule": {"requested_gammas": [0.0, 0.5], "steps": 5},
        },
        "records": records,
    }


def test_known_contact_minus_null_differences_are_preserved_and_summarized():
    report = analyze_collection(_collection(), bootstrap_seed=7, bootstrap_resamples=50)

    gamma_zero = report["by_requested_gamma"][0]["metrics"]
    assert gamma_zero["dominance"]["per_replicate_contact_minus_null"] == [1.0, 2.0]
    assert gamma_zero["dominance"]["descriptive_summary"]["mean"] == 1.5
    assert gamma_zero["effective_cluster_count"]["per_replicate_contact_minus_null"] == [2.0, 4.0]
    assert gamma_zero["entropy"]["per_replicate_contact_minus_null"] == [-1.0, -2.0]
    assert gamma_zero["kernel.churn"]["per_replicate_contact_minus_null"] == [3.0, 6.0]
    assert len(report["per_pair"]) == 4
    assert report["per_pair"][0]["metrics"]["kernel.topo_similarity"]["contact_minus_null"] == 4.0
    assert report["validation"]["passed"] is True
    assert "no causal inference is made" in report["interpretation"]
    json.loads(serialize_report(report))


def test_fingerprint_mismatch_is_rejected():
    collection = _collection()
    collection["records"][1]["initial_state_fingerprint"] = "not-the-matched-state"

    with pytest.raises(CollectionValidationError, match="mismatched initial fingerprints"):
        validate_raw_collection(collection)


def test_bootstrap_is_deterministic_for_a_fixed_seed():
    first = analyze_collection(_collection(), bootstrap_seed=42, bootstrap_resamples=100)
    second = analyze_collection(_collection(), bootstrap_seed=42, bootstrap_resamples=100)

    assert first == second
    assert serialize_report(first) == serialize_report(second)


def test_cli_writes_strict_json_and_refuses_overwrite(tmp_path):
    input_path = tmp_path / "raw.json"
    output_path = tmp_path / "report.json"
    input_path.write_text(json.dumps(_collection()), encoding="utf-8")

    assert main([
        "--input", str(input_path), "--output", str(output_path),
        "--bootstrap-resamples", "5",
    ]) == 0
    original = output_path.read_text(encoding="utf-8")
    assert json.loads(original)["validation"]["passed"] is True

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        main([
            "--input", str(input_path), "--output", str(output_path),
            "--bootstrap-resamples", "5",
        ])
    assert output_path.read_text(encoding="utf-8") == original
