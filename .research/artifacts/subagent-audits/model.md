## Forensic audit — claims unproven

### Exact code/paper mismatches

- **Beliefs do not mutate.** Paper requires Gaussian perturbation of each participating belief vector (`paper/gods_as_centroids_v2.md:101-110`). Kernel “mutation” only creates/mutates *forms* (`sim/swarm_kernel.py:588-597`); beliefs change only via coercive centroid pull, prophets, or generational reset (`:905-925`, `:600-628`, `:743-769`). Thus claims parameterized by doctrinal mutation μ are unsupported.
- **Prestige equation differs.** Paper specifies additive \(w\leftarrow w+\alpha(\mathbf1(success)-.5)\) (`paper/...md:98-100`); code applies asymmetric multiplicative growth/decay, clamped to `[.1,10]` (`sim/swarm_kernel.py:513-516`). This changes concentration and all prestige-convergence claims.
- **Fusion omits a required condition.** Definition 9 requires proximity **and recent membership exchange** (`paper/...md:142-149`). Code merges solely on distance, with a coercion-expanded threshold (`sim/swarm_kernel.py:560-583`); no membership history exists.
- **Accessibility success path is a no-op.** `interact()` computes `projected_ctx` then discards it, scoring prediction against the unrestricted context (`sim/swarm_kernel.py:482-492`). Restrictions only alter learning, not interpretation/success. Also channel noise uses module-global RNG, breaking seed reproducibility (`:272-276`).
- **“Uniform sphere” is false.** `rnd_unit_vec()` samples independent `[0,1)` coordinates, then normalizes: positive orthant only, not a uniform sphere. Prophet code explicitly claims the latter (`sim/swarm_kernel.py:608-610`; paper Definition 11 at `:164-175`).
- **Priors constrain the purportedly emergent result.** Every agent begins from a mixture of hand-authored deity vectors and receives associations for every theonym (`sim/swarm_kernel.py:357-383`); production is directly biased by belief (`:455-469`). The paper says priors are naming seeds that “do not constrain dynamics” (`paper/...md:62-80`). The code contains 24 priors, not the stated 12, and never names centroids from nearest priors.
- **The corpus-calibrated configuration is inert.** `sim/corpus_calibrated_config.json` nests actual parameters under `"parameters"` and priors under `"deity_priors"`; `sim/run.py:20-26` accepts only matching top-level `Config` fields. None of its calibrated values or priors reach `SwarmKernel`.
- **Declared network modes are ignored.** `Config.social_network` advertises random/small-world/preferential (`sim/swarm_kernel.py:142`), but `_build_social_network()` always builds Watts–Strogatz (`:397-415`). Therefore `sim/configs/no_priors.json`’s `"random"` setting has no effect.
- **Generation transmission contradicts cultural inheritance.** One mentor draw is shared by every child; child beliefs are fresh random draws, not inherited (`sim/swarm_kernel.py:743-765`). It also omits sensory channels. Any multi-generation belief/lock-in interpretation is invalid.
- **Hysteresis experiment is not a hysteresis protocol.** “Reverse” starts a newly initialized kernel with `seed + 1`, rather than the final forward state (`sim/hysteresis_sweep.py:141-145`). It compares distinct initial conditions, not forward/reverse trajectories. Hence paper hysteresis results (`paper/...md:214-241`) are unsubstantiated.
- **Published prophet-escape results use a different model.** `sim/prophet_escape_modal.py` defines `MiniKernel` (`:77+`): all-to-all hearer selection (`:124-131`), random contexts (`:121-122`), and actual Gaussian belief mutation (`:197-201`), unlike `SwarmKernel`. It cannot validate paper claims about the repository kernel.

### Result-baking mechanisms

- Coercion directly enlarges both assignment radius and fusion radius (`sim/swarm_kernel.py:519-521`, `:560-566`), then mechanically pulls every clustered belief to its centroid (`:905-925`). Fewer clusters at high γ are encoded operations, not an independently demonstrated emergent phase transition.
- Comparison configs additionally change the outcome metric’s threshold: low coercion uses `cluster_threshold=0.6`, high uses `0.3` (`sim/configs/low_coercion.json:29`, `sim/configs/high_coercion.json:29`). They are not controlled γ experiments.
- Greedy, agent-order-dependent threshold clustering (`sim/swarm_kernel.py:525-536`) plus automatic proximity merger can create/remove “deities” without any social dynamical event.
- Ritual raises the success threshold (`:490-492`), causing more failure/negative learning; it does not model shared ritual content or coordination. The tested outcome is cluster-count variance, not the claimed 40% centroid-drift reduction (`tests/test_paper_claims.py:189-219`; paper `:261-263`).
- Current tests are smoke assertions, often merely `len(centroids) >= 1` (`tests/test_paper_claims.py:82-100`, `:146-153`) or permissive inequalities; saved-result tests only check that image files exist (`:340-362`). They do not reproduce stated samples, thresholds, effect sizes, null controls, or confidence intervals.

## Canonical model v2: state transitions

Use one declared state: agent \(i=(b_i,w_i,\ell_i,S_i)\), association lexicon \(\ell_i\), fixed graph \(G\), and persistent cluster labels/history.

Per tick:

1. Sample context and select speaker by normalized prestige; select distinct neighbors under the declared graph mechanism.
2. Speaker emits forms from its lexicon; each hearer projects both context and message into its accessible subspace.
3. Compute success in that same projected space; update lexica only from the explicit success/failure rule.
4. Update prestige using one documented equation, once per unique participant.
5. Update participating beliefs with the declared social-learning term plus seeded bounded/Gaussian belief noise; normalize. `mutation_rate` must mean this and only this.
6. At cluster epochs, cluster from beliefs using an order-invariant specified algorithm; record labels.
7. Apply fusion only when distance **and measured recent cross-cluster exchange** meet pre-registered thresholds. Apply fission from its stated variance rule. Apply coercion through one pre-specified causal mechanism, not outcome-dependent clustering thresholds.
8. Prophecy samples from the intended distribution, assigns declared prestige, and pulls the declared population.
9. At generation boundaries, each child independently samples mentors and inherits specified belief/lexicon/channel traits; rebuild or retain network explicitly.
10. Compute \(D,N_\mathrm{eff},H\), centroid displacement, exchange, and uncertainty from saved trajectories.

## Minimal implementation order

1. Specify v2 equations, parameter semantics, invariants, RNG ownership, and the causal role of γ.
2. Fix reproducibility and configuration loading; reject unknown/nested inactive parameters.
3. Implement belief mutation and unify `SwarmKernel`; delete or clearly isolate divergent `MiniKernel` experiment code.
4. Fix sensory projection/success scoring and implement actual network modes.
5. Implement order-invariant clustering, label history, exchange-gated fusion, and correctly inherited generations.
6. Replace experiment protocols with controlled, preregistered multi-seed sweeps; reverse hysteresis must continue each forward terminal state.
7. Recompute all figures and downgrade/remove unsupported paper numbers.

## Acceptance tests

- **Determinism:** same config/seed yields byte-identical trajectories; sensory-noise runs are reproducible.
- **Mutation isolation:** with social pull, prophets, and generations disabled, μ>0 changes participant beliefs with expected nonzero variance; μ=0 changes none.
- **Accessibility:** restricted-agent success is evaluated against its projection; a deliberately orthogonal inaccessible-axis context changes unrestricted but not restricted score.
- **Configuration:** every shipped JSON changes the intended runtime field; corpus JSON either loads calibrated values/priors or fails loudly.
- **Network:** random, small-world, and preferential modes have demonstrably different graph statistics.
- **Fusion:** close clusters with zero exchange do not merge; sufficient exchange plus proximity does.
- **Coercion ablation:** estimate \(D,N_\mathrm{eff}\) over preregistered seeds with γ as the sole changed parameter; separately report effects of radius widening, merger widening, and centroid pull.
- **Hysteresis:** each reverse sweep starts from its own forward γ=1 terminal state; report paired trajectories, CIs, and a null model. No “first-order” claim absent discontinuity/coexistence evidence.
- **Paper-result gates:** tests must assert the paper’s stated sample sizes/effect sizes—e.g., 30-run \(D>0.99\), accessibility centroid-distance `<.05`, ritual 40% displacement reduction—or the prose must label them unverified.
