import json

import pytest

from sim.experiments.modal_canonical_hysteresis_analysis import (
    CollectionValidationError,
    analyze_collection,
    main,
    validate_raw_collection,
)


def _collection():
    records = []
    # Replicate 0 has a triangular descending-minus-ascending contrast: area 1.
    for replicate, ascending, descending in ((0, (0, 0, 0), (0, 1, 0)), (1, (1, 1, 1), (1, 1, 1))):
        for gamma, dominance in zip((0.0, 1.0, 2.0), ascending):
            records.append({"replicate": replicate, "direction": "ascending", "gamma": gamma, "dominance": dominance})
        for gamma, dominance in zip((2.0, 1.0, 0.0), reversed(descending)):
            records.append({"replicate": replicate, "direction": "descending", "gamma": gamma, "dominance": dominance})
    return {"metadata": {"gamma_schedule": [0.0, 1.0, 2.0], "replicate_count": 2}, "records": records}


def test_analyzer_calculates_known_signed_trapezoidal_loop_areas_and_contrasts():
    report = analyze_collection(_collection(), bootstrap_resamples=50, bootstrap_seed=9)

    assert [item["loop_area"] for item in report["per_replicate"]] == [1.0, 0.0]
    assert report["loop_area_summary"]["mean"] == 0.5
    assert report["contrasts_by_gamma"][1]["per_replicate_descending_minus_ascending"] == [1.0, 0.0]
    assert report["contrasts_by_gamma"][1]["summary"]["mean"] == 0.5
    assert report["validation"] == {"passed": True, "failures": [], "warnings": []}
    assert "does not infer a phase transition or hysteresis conclusion" in report["interpretation"]


def test_bootstrap_is_deterministic_for_a_fixed_seed():
    first = analyze_collection(_collection(), bootstrap_seed=42, bootstrap_resamples=100)
    second = analyze_collection(_collection(), bootstrap_seed=42, bootstrap_resamples=100)

    assert first == second


def test_malformed_pairing_is_rejected():
    raw = _collection()
    raw["records"] = [record for record in raw["records"] if not (record["replicate"] == 1 and record["direction"] == "descending" and record["gamma"] == 2.0)]

    with pytest.raises(CollectionValidationError, match="replicate_count|not paired"):
        validate_raw_collection(raw)


def test_cli_refuses_to_overwrite_existing_report(tmp_path):
    input_path = tmp_path / "raw.json"
    output_path = tmp_path / "report.json"
    input_path.write_text(json.dumps(_collection()), encoding="utf-8")
    output_path.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        main(["--input", str(input_path), "--output", str(output_path), "--bootstrap-resamples", "5"])
    assert output_path.read_text(encoding="utf-8") == "existing"
