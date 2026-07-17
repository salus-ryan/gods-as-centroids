# Canonical Model v2 Specification

**Status:** approved implementation target  
**Scope:** Python canonical kernel first. Existing simulations, figures, ports, and paper claims are legacy until reproduced by this specification.

## 1. Scope and claim boundary

v2 is an exploratory agent-based model of social-belief clustering. A *godform* is a model-defined prestige-weighted centroid; it is not a measurement of a deity, a tradition, or human belief. The model may generate hypotheses about social mechanisms. It does not validate historical causation without independent data.

## 2. State

At time `t`, each agent has:

- `belief`: unit vector in the declared 12-axis space;
- `prestige`: positive bounded scalar;
- `lexicon`: form-to-semantic association map and frequencies;
- `channels`: available observation channels;
- `cluster_label`: persistent label from the previous cluster epoch.

Global state contains one graph, one seeded random-number source, an event log, cluster labels/history, and an immutable resolved configuration.

## 3. Tick order

1. Sample a context from the declared context distribution.
2. Select one speaker by prestige; select distinct graph neighbors by the active contact rule.
3. Produce a message from the speaker lexicon.
4. Project both context and message into each hearer's accessible subspace. Compute that hearer's success in the same subspace.
5. Update lexica from the documented success/failure rule.
6. Update each unique participant's prestige exactly once with one documented bounded update rule.
7. Update each participating belief with social learning plus belief noise. `mutation_rate` means only this noise magnitude.
8. On a cluster epoch, apply a fixed, order-invariant clustering method. Persist labels and membership history.
9. Apply fusion only if predeclared semantic proximity **and** measured recent cross-cluster exchange conditions hold. Apply fission by its stated variance rule.
10. Apply an explicit prophet intervention only when scheduled; record all components (novelty, prestige, recruitment) separately.
11. At a generation boundary, independently sample mentors for each child and inherit defined belief/lexicon/channel state.

## 4. Coercion

`coercion` must not change a clustering or merge threshold in the primary model. It represents one or more declared causal mechanisms selected explicitly by configuration:

- `contact_homophily`: modifies neighbor-selection weights;
- `institutional_pull`: pulls lower-prestige agents toward a specified institutional centroid;
- `dissent_cost`: affects prestige/transmission of non-institutional beliefs;
- `none`: null control.

Each mechanism is separately switchable for ablations. Cluster measurements use gamma-invariant settings.

## 5. Reproducibility invariants

- All stochasticity uses kernel-owned RNG streams derived from a recorded master seed.
- Same resolved config, seed, and code revision yield the same serialized trajectory.
- Config loading rejects unknown keys and explicitly supports nested calibrated parameter files only through a conversion function.
- Every run writes resolved config, seeds, commit, environment, event log, time series, and terminal serialized state.

## 6. Required v2 tests before claim experiments

1. Deterministic replay.
2. `mutation_rate=0` leaves beliefs unchanged when other belief mechanisms are disabled; positive mutation changes them.
3. Distinct declared network modes produce distinct graph statistics.
4. Restricted success is evaluated in restricted space.
5. Fusion cannot occur without exchange; it can occur with sufficient exchange plus proximity.
6. Config values demonstrably reach runtime state.
7. Generation inheritance preserves specified parent-derived traits.
8. Hysteresis reverse branch begins from the exact serialized forward terminal state.

## 7. Deferred work

Lattice, autoencoder, web, C++/Go/Rust ports, and paper figures remain out of scope until this canonical kernel and its experiment runner pass the required tests.
