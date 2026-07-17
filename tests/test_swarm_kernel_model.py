import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))

from swarm_kernel import AXES, Config, Context, SwarmKernel, norm, rnd_unit_vec


def _beliefs(kernel):
    return [tuple(agent.belief[axis] for axis in AXES) for agent in kernel.agents]


def _graph_edges(kernel):
    return tuple((node, tuple(neighbors)) for node, neighbors in kernel.social_graph.items())


def test_restricted_success_ignores_an_inaccessible_axis():
    kernel = SwarmKernel(Config(N=2, seed=123, base_success_thresh=0.8, channel_noise=0.0))
    speaker, hearer = kernel.agents
    hearer.sensory_channels = ["sight"]
    hearer.assoc["signal"] = {
        axis: (1.0 if axis == "nature" else -10.0 if axis == "authority" else 0.0)
        for axis in AXES
    }
    ctx = Context("forage", "hunter", "forest", "dawn", {
        axis: 1.0 if axis == "nature" else 0.0 for axis in AXES
    })

    # Authority is inaccessible through sight, so the projected message and
    # context are identical despite their incompatible full-space vectors.
    assert kernel.interact(speaker, [hearer], ctx, ["signal"])


def test_unrestricted_success_uses_full_space_comparison():
    kernel = SwarmKernel(Config(N=2, seed=123, base_success_thresh=0.8, channel_noise=0.0))
    speaker, hearer = kernel.agents
    hearer.assoc["signal"] = {
        axis: (1.0 if axis == "nature" else -10.0 if axis == "authority" else 0.0)
        for axis in AXES
    }
    ctx = Context("forage", "hunter", "forest", "dawn", {
        axis: 1.0 if axis == "nature" else 0.0 for axis in AXES
    })

    assert not kernel.interact(speaker, [hearer], ctx, ["signal"])


def test_projection_noise_uses_kernel_rng_and_replays_deterministically():
    cfg = Config(
        N=8,
        seed=123,
        enable_sensory_restrictions=True,
        sensory_restriction_ratio=1.0,
        channel_noise=0.2,
    )
    first, second = SwarmKernel(cfg), SwarmKernel(cfg)
    first_successes = [first.step().success for _ in range(12)]

    # Module-level random state must not affect kernel trajectories.
    random.seed(99999)
    second_successes = [second.step().success for _ in range(12)]
    assert first_successes == second_successes
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


def _axis_belief(axis, value=1.0):
    return {name: value if name == axis else 0.0 for name in AXES}


def test_clustering_is_identical_for_equal_states_at_zero_and_full_coercion():
    configs = [
        Config(N=4, seed=18, use_deity_priors=False, coercion=gamma,
               cluster_threshold=0.4, fission_min_cluster_size=99)
        for gamma in (0.0, 1.0)
    ]
    kernels = [SwarmKernel(cfg) for cfg in configs]
    second_group = {
        axis: (0.5 if axis == "authority" else math.sqrt(0.75) if axis == "justice" else 0.0)
        for axis in AXES
    }
    for kernel in kernels:
        for agent in kernel.agents[:2]:
            agent.belief = _axis_belief("authority")
        for agent in kernel.agents[2:]:
            agent.belief = dict(second_group)
        kernel._update_clusters()

    # The groups are 0.5 cosine-distance apart: separate under the fixed
    # cluster threshold, regardless of contact-homophily strength.
    assert kernels[0].clusters == [[0, 1], [2, 3]]
    assert kernels[1].clusters == kernels[0].clusters
    assert kernels[1].centroids == kernels[0].centroids


def test_coercion_deterministically_weights_contact_selection_by_homophily():
    def contact_trace(coercion):
        kernel = SwarmKernel(Config(N=4, seed=29, use_deity_priors=False, coercion=coercion))
        speaker, similar, neutral, dissimilar = kernel.agents
        speaker.belief = _axis_belief("authority")
        similar.belief = _axis_belief("authority")
        neutral.belief = _axis_belief("justice")
        dissimilar.belief = _axis_belief("authority", -1.0)
        kernel.social_graph = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}
        return [hearer.id for _ in range(20) for hearer in kernel._select_hearers(speaker)]

    uniform_trace = contact_trace(0.0)
    weighted_trace = contact_trace(1.0)

    assert weighted_trace == contact_trace(1.0)
    assert weighted_trace != uniform_trace
    assert weighted_trace.count(1) > weighted_trace.count(3)
