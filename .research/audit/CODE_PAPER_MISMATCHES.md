# Baseline Code–Paper Mismatches

**Baseline:** `268af3c`  
**Severity:** P0 blocks research claims; P1 blocks reproducibility/interpretation; P2 is documentation debt.

| ID | Severity | Paper/model statement | Baseline implementation | Resolution target |
|---|---|---|---|---|
| M-01 | P0 | Hysteresis reverse sweep follows the forward terminal state. | `sim/hysteresis_modal.py` creates a new `MiniKernel` for each direction (`do_sweep`), with a distinct seed. | One canonical kernel; retain exact state at γ=1 then reverse it. |
| M-02 | P0 | Coercion is a social field causing attractor deepening. | `sim/swarm_kernel.py` directly increases clustering assignment threshold and merge distance with coercion. | Replace outcome-coupled geometry with explicit social mechanisms; ablate each mechanism. |
| M-03 | P0 | Published simulation results arise from the model described in the paper. | `sim/hysteresis_modal.py` contains an independent `MiniKernel` with materially different dynamics. | Eliminate duplicated kernels; experiments import canonical package. |
| M-04 | P1 | Beliefs mutate continuously by Gaussian perturbation. | Main `mutate_agent()` mutates symbolic forms/associations, not `Agent.belief`; direct belief change occurs mainly under centroid pull, prophets, and generation reset. | Implement a specified belief update or rewrite the model description. |
| M-05 | P1 | Fusion requires centroid proximity and agent exchange. | Fusion checks centroid proximity only. | Measure contact/membership exchange and require the stated condition, or revise definition. |
| M-06 | P1 | Prestige update is additive. | `update_prestige()` applies multiplicative bounded updates. | Choose one formulation; align equation, code, and tests. |
| M-07 | P1 | Coercion deepens the dominant basin. | Cluster pull is toward every cluster's own centroid; merge/radius rules perform most consolidation. | Specify a defensible, testable enforcement/centralization mechanism. |
| M-08 | P1 | Sensory restriction changes observation/communication. | `interact()` computes restricted context but compares predictions with full context; test checks counts rather than attractor equivalence. | Define observation likelihood and evaluate centroid/belief correspondence. |
| M-09 | P1 | Seeded simulations are reproducible. | `Agent.project_context()` uses module-level `random.gauss` instead of kernel RNG. | Use only `self.rng`/injected RNG and add same-seed regression tests. |
| M-10 | P1 | Deity priors and corpus-derived tradition centroids are consistent. | Paper table, code priors, and calibration-generated priors differ in cardinality/content/role. | Separate hand-authored illustrative priors from annotation-derived data and version both. |
| M-11 | P2 | Seshat-derived coercion schedule is empirical. | `estimate_coercion_schedule()` contains hand-authored dated values; no Seshat import/fitting path. | Integrate an actual versioned dataset or relabel as historical scenario. |
| M-12 | P2 | Tests verify paper claims. | `tests/test_paper_claims.py` is largely a smoke/file-presence suite with permissive qualitative checks. | Replace with invariant, replication, ablation, and predeclared statistical tests. |

## Invariant for v2

The canonical implementation, paper equations, experiment configuration, raw data, generated figures, and tests must be traceable to the same versioned model identifier.
