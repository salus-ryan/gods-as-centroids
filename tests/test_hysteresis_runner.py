from sim.experiments.hysteresis_runner import run_hysteresis_schedule
from sim.swarm_kernel import Config


def _records(seed=19):
    return run_hysteresis_schedule(
        [0.0, 0.5, 1.0],
        seed=seed,
        steps_per_gamma=3,
        config=Config(
            N=10,
            cluster_update_freq=2,
            steps_per_generation=10_000,
            mutation_rate=0.02,
        ),
    )


def test_descending_branch_starts_at_exact_forward_terminal_state():
    records = _records()
    forward = [record for record in records if record["direction"] == "ascending"]
    descending = [record for record in records if record["direction"] == "descending"]

    assert descending[0]["gamma"] == forward[-1]["gamma"]
    assert descending[0]["starting_state_fingerprint"] == forward[-1]["state_fingerprint"]


def test_records_are_deterministic_for_same_seed():
    assert _records(41) == _records(41)
