import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim"))

import run


def test_plain_config_values_are_applied(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"N": 9, "seed": 123, "mutation_rate": 0.0}))

    cfg = run.load_config(config_path)

    assert cfg.N == 9
    assert cfg.seed == 123
    assert cfg.mutation_rate == 0.0


def test_unknown_config_key_fails(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"N": 9, "not_a_config_key": True}))

    with pytest.raises(ValueError, match=r"Unknown Config key\(s\): not_a_config_key"):
        run.load_config(config_path)


def test_corpus_calibrated_wrapper_fails_clearly():
    wrapper_path = ROOT / "sim" / "corpus_calibrated_config.json"

    with pytest.raises(ValueError, match="Corpus-calibrated wrapper configs"):
        run.load_config(wrapper_path)


def test_run_writes_resolved_provenance(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"N": 2, "seed": 321, "mutation_rate": 0.0}))
    outdir = tmp_path / "runs"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run.py",
            "--config", str(config_path),
            "--steps", "0",
            "--outdir", str(outdir),
            "--label", "provenance-test",
        ],
    )

    run.main()

    provenance_path = next(outdir.glob("*/provenance.json"))
    provenance = json.loads(provenance_path.read_text())
    assert provenance["config"]["N"] == 2
    assert provenance["config"]["mutation_rate"] == 0.0
    assert provenance["requested_steps"] == 0
    assert provenance["seed"] == 321
    assert "git_revision" in provenance
    assert provenance["python"]["version"]
    assert provenance["platform"]["platform"]
