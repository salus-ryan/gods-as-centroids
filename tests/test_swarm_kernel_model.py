import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))

from swarm_kernel import AXES, Config, SwarmKernel, norm, rnd_unit_vec


def _beliefs(kernel):
    return [tuple(agent.belief[axis] for axis in AXES) for agent in kernel.agents]


def _graph_edges(kernel):
    return tuple((node, tuple(neighbors)) for node, neighbors in kernel.social_graph.items())


def test_projection_noise_uses_kernel_rng_and_replays_deterministically():
    cfg = Config(
        N=8,
        seed=123,
        enable_sensory_restrictions=True,
        sensory_restriction_ratio=1.0,
        channel_noise=0.2,
    )
    first, second = SwarmKernel(cfg), SwarmKernel(cfg)
    first.run(12)

    # Module-level random state must not affect kernel trajectories.
    random.seed(99999)
    second.run(12)
    assert _beliefs(first) == _beliefs(second)
    assert first.tokens == second.tokens


def test_projection_noise_requires_an_injected_rng():
    kernel = SwarmKernel(Config(N=2, seed=1))
    kernel.agents[0].sensory_channels = ["sight"]
    with pytest.raises(ValueError, match="kernel-owned RNG"):
        kernel.agents[0].project_context({axis: 1.0 for axis in AXES}, noise=0.1)


def test_mutation_rate_is_belief_noise_and_form_mutation_is_separate():
    no_noise = SwarmKernel(Config(N=3, seed=4, mutation_rate=0.0, form_mutation_rate=0.0))
    original = dict(no_noise.agents[0].belief)
    no_noise.mutate_belief(no_noise.agents[0])
    no_noise.mutate_agent(no_noise.agents[0])
    assert no_noise.agents[0].belief == original

    noisy = SwarmKernel(Config(N=3, seed=4, mutation_rate=0.3, form_mutation_rate=0.0))
    original = dict(noisy.agents[0].belief)
    noisy.mutate_belief(noisy.agents[0])
    assert noisy.agents[0].belief != original
    assert math.isclose(norm(noisy.agents[0].belief), 1.0)
    assert Config().form_mutation_rate == 0.08


def test_rnd_unit_vec_covers_full_unit_sphere():
    rng = random.Random(9)
    samples = [rnd_unit_vec(rng) for _ in range(200)]
    assert all(math.isclose(norm(sample), 1.0) for sample in samples)
    assert all(any(sample[axis] < 0.0 for sample in samples) for axis in AXES)
    assert all(any(sample[axis] > 0.0 for sample in samples) for axis in AXES)


@pytest.mark.parametrize("mode", ["random", "small_world", "preferential"])
def test_network_modes_build_simple_undirected_graphs(mode):
    kernel = SwarmKernel(Config(N=30, seed=27, social_network=mode, social_k=4, social_p=0.2))
    for node, neighbors in kernel.social_graph.items():
        assert node not in neighbors
        assert len(neighbors) == len(set(neighbors))
        assert all(node in kernel.social_graph[neighbor] for neighbor in neighbors)


def test_network_modes_are_deterministic_and_distinct():
    graphs = {}
    for mode in ("random", "small_world", "preferential"):
        cfg = Config(N=30, seed=27, social_network=mode, social_k=4, social_p=0.2)
        graphs[mode] = _graph_edges(SwarmKernel(cfg))
        assert graphs[mode] == _graph_edges(SwarmKernel(cfg))
    assert len(set(graphs.values())) == 3
