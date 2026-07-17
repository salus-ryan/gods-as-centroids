## Methods review — figures are not evidentially adequate

No files changed.

### Blocking defects

1. **The headline hysteresis figure is not a hysteresis experiment.**  
   Both `sim/hysteresis_sweep.py` and `sim/hysteresis_modal.py` construct a *new* kernel for the reverse path. In the local script, `run_sweep()` always creates `SwarmKernel(cfg)` (`sim/hysteresis_sweep.py:79-97`), and the reverse run is invoked with a new seed (`:140-146`). The Modal version does the same (`sim/hysteresis_modal.py:367-387`). Thus reverse points do not inherit the terminal forward state; they are an independently initialized system equilibrated at γ=1. A difference between curves is not memory/path dependence.

2. **The claimed phase transition is partly encoded in the measurement algorithm.**  
   Coercion directly expands the clustering assignment radius (`effective_threshold = cluster_threshold + 0.3*coercion`) in `sim/swarm_kernel.py:519-536`, and the model directly merges centroids with an expanding coercion-dependent cutoff (`merge_dist = 0.15 + 0.35*coercion`; see `:556-590`). Since dominance and \(N_\mathrm{eff}\) are computed from these clusters, the plotted outcome is mechanically sensitive to γ even absent a dynamical transition. This invalidates causal claims that γ *emergently* produces monotheistic collapse unless separated from this definition.

3. **Threshold crossings are post-hoc descriptive labels, not statistical estimates.**  
   The figures identify “critical points” as the first mean dominance above 0.7 (`sim/hysteresis_sweep.py:380-400`); no rationale, individual-run crossing distribution, CI, null test, or multiplicity control is provided. Standard-deviation ribbons are not confidence intervals and do not address serial correlation in the 20 measurements within each 500-step window (`:102-114`).

4. **Saved “raw” hysteresis and lattice data are aggregates, not raw replicates.**  
   `hysteresis_data.json` stores only per-γ mean/SD aggregates (`sim/hysteresis_sweep.py:343-357`), as does lattice output (`sim/lattice_hysteresis_modal.py:727-742`). Seeds, trajectories, terminal states, per-replicate loop areas, code revision, and RNG/environment provenance are lost. The figures therefore cannot be independently reanalyzed.

5. **Tests are not claim-validation tests.**  
   The test module calls itself smoke tests (`tests/test_paper_claims.py:5-10`). Several assertions are permissive one-seed or weak directional checks—for example “high γ has no more than two extra clusters” (`:123-131`), “prophets” merely leave at least one centroid (`:146-153`), and ritual is allowed to double variance (`:216-220`). Figure “tests” only assert PNG existence (`:340-356`). These cannot validate paper claims or catch the reverse-state bug.

### Figure-specific problems

#### Hysteresis / hero plot
- Reverse reset is fatal, as above. The existing output actually reflects that protocol, not carryover.
- No stationarity diagnosis: “equilibration” is asserted rather than demonstrated; fixed 2,000-step dwell and a 500-step average are used (`sim/hysteresis_sweep.py:102-114`).
- No sweep-rate, dwell-time, γ-grid, initialization, network, or parameter sensitivity analysis.
- The primary model has many coupled γ pathways (contact selection plus cluster/deepening/merging); no ablation isolates them.
- The model uses hand-specified deity priors (`sim/swarm_kernel.py:352-372`), while “corpus calibrated” is not a demonstrated calibration/holdout procedure.

#### Finite-size figure
- This is the only sweep implementation with true forward→reverse state carryover (`sim/finite_size_modal.py:297-319`), but it is still insufficient for a finite-size/first-order claim.
- It changes the cluster threshold with N (`theta_eff = 0.12*(80/N)^0.25`, `:283-290`), confounding system size with the observable’s clustering rule.
- It uses a separate inline `MiniKernel` with random positive-vector initialization (`sim/finite_size_modal.py:70-98`), not `SwarmKernel` or the deity-prior setup used in the headline hysteresis experiment. Results are therefore not directly comparable.
- Only N={80,200,500}, 15 runs, a single sweep rate, and one final measurement per γ are used (`:380-392`; `:297-313`). There is no finite-size scaling model, uncertainty on slopes/crossings, susceptibility/bimodality analysis, Binder-type diagnostic, or extrapolation.
- “Max slope” is computed from the mean curve (`:449-453`) rather than per-run estimates; the reported gap also treats `0.0` as false (`:455-460`).

#### Lattice-versus-arithmetic figure
- It repeats the invalid reverse reset: fresh `LatticeKernel` instances are created for both directions (`sim/lattice_hysteresis_modal.py:543-572`).
- Hamming and arithmetic conditions use different seed families (`SEED_BASE` versus `SEED_BASE+10000`; `:664-678`), eliminating paired comparisons and adding Monte-Carlo noise to the alleged representation effect.
- The clustering metric changes from cosine distance to normalized 96-bit Hamming distance (`:401-408`), but the same numerical threshold is reused. This is not a calibrated comparison of equivalent resolutions.
- The lattice version decodes Hamming centroids back into continuous vectors for coercive attraction (`:431-434`, `:370-383`), so it is not a pure discrete/snap-dynamics intervention.
- Coercion again directly increases both assignment and fusion cutoffs (`:385-387`, `:436-449`).
- Existing lattice aggregate data begin already near monodominance at γ=0 (Hamming \(D\approx0.90\) in `sim/runs/lattice_hysteresis/lattice_hysteresis_data.json`), so a “sharper transition” claim is not supported. A lower crossing threshold is not a sharpness statistic.

#### Prophet-escape figure
- “Escape” is an unvalidated, arbitrary final-time conjunction, \(N_\mathrm{eff}\ge3\) and \(D<0.5\) (`sim/prophet_escape_modal.py:413-424`), with no persistence or time-to-escape criterion.
- There is no eligibility check that each phase-1 replicate actually reaches the prespecified locked state before testing escape (`:388-396`).
- The intervention is a bundled oracle: it replaces one belief with a random vector, gives prestige 4, and forcibly moves 15% of the most similar agents (`sim/prophet_escape_modal.py:203-214`). It cannot identify an effect of “prophet events” rather than random reset, prestige, or forced recruitment.
- The no-prophet baseline pools all mutation rates (`:588-591`), hence is confounded by μ. The advertised prophet-only condition μ=0.08 is absent from the grid, which is `[0.05, .10, .15, .20, .25]` (`:518-520`) and therefore never reported (`:606-611`).
- The “best condition” is selected from 30 cells with no held-out confirmation or multiple-comparison adjustment (`:593-604`).
- Seeds depend on treatment values (`:386`), preventing paired/common-random-number contrasts.
- The plotted caption is factually inconsistent with execution: caption says 3,000 γ=.9 then 5,000 γ=0 (`:505-507`); code runs 5,000 γ=.9 then 8,000 γ=.05 (`:379-400`).

## Redesigned protocol

### 1. Pre-register estimands and acceptance criteria
Primary:
- **Hysteresis loop area per replicate**: \(A_r=\int_0^1[D_{r,\downarrow}(\gamma)-D_{r,\uparrow}(\gamma)]\,d\gamma\), trapezoidally estimated on the fixed grid.
- **Path-memory contrast** at each γ: paired \(D_\downarrow-D_\uparrow\), plus \(N_\mathrm{eff}\), entropy, and an independent, fixed clustering metric.
- **Critical points**: per-replicate interpolated crossings under a predeclared \(D\) threshold, reported only as a secondary descriptive measure.

Acceptance for a hysteresis claim: 95% paired-bootstrap CI for median loop area excludes 0, a two-sided within-replicate permutation/sign-flip test controls family-wise error for the γ-wise contrasts, and the sign persists over a predeclared contiguous γ interval and across sweep-rate/dwell sensitivity analyses.

For prophet escape: predeclare a lock-in eligibility rule, a sustained escape rule (e.g., escape criteria continuously met for ≥K post-intervention measurements), and survival/time-to-escape as primary rather than final state alone.

### 2. Genuine state-carryover hysteresis
For each master seed:
1. Initialize once; equilibrate at γ=0 using predeclared convergence diagnostics.
2. Ramp 0→1; retain the exact kernel object, agent state, social graph, associations, cluster state, and RNG stream.
3. At γ=1, immediately ramp 1→0 on that same object.
4. Record full time series, terminal snapshots at every γ, and enough state to resume/replay.
5. Separately run descending-only paths initialized/equilibrated at γ=1. Label these **initial-condition controls**, not the reverse branch of a loop.
6. Repeat for at least three dwell durations and three γ increments/rates. A loop that vanishes with longer dwell is finite-time lag, not evidence of equilibrium bistability.

### 3. Factorial ablations and baselines
Use the same initial states and paired RNG streams where possible.

**Coercion mechanism ablation**
- contact-choice weighting only;
- attractor pull only;
- cluster assignment/merge cutoff fixed;
- current full model;
- null γ that changes no dynamics but is passed through plotting/analysis.

The primary outcome must also be measured using a γ-invariant, order-independent clustering method with thresholds frozen before the sweep (and preferably a continuous concentration measure such as pairwise similarity, largest eigenvalue, or effective-number entropy).

**Lattice**
- Calibrate Hamming and cosine clustering thresholds on held-out initial-state data to equal baseline cluster-number/false-merge rates.
- Compare arithmetic versus lattice using the same states, graph, schedule, and matched random streams.
- Separate: encoding only; Hamming clustering only; Hamming centroid only; decode-and-pull only; full lattice.
- Report reconstruction error, assignment agreement, threshold sensitivity, tie handling, and representation-induced baseline dominance.

**Prophet**
A factorial design: event occurrence × prestige boost × recruitment/pull × vector novelty × μ. Include:
- null event (same timing and RNG consumption, no state change);
- random-vector-only;
- prestige-only;
- pull-only;
- mutation-only;
- matched expected event-count/dose conditions.
Analyze realized event count and timing, not rate alone. Use a stratified baseline at each μ, not a pooled baseline.

**Finite size**
Hold all microscopic and measurement parameters fixed across N. If a threshold must vary, make that a separate robustness analysis—not the primary finite-size result. Use a broader, predeclared N grid and several random graph realizations per seed; estimate scaling with uncertainty rather than visually comparing three curves.

### 4. Statistical reporting
- Select replication count from a pilot-based power/precision target for loop area and escape-risk difference; 15–30 arbitrary runs is not a criterion.
- Report all replicate distributions, not only mean±SD: spaghetti/violin plots, bootstrap CIs, effect sizes, and exact seed counts.
- Treat within-window samples as time series; estimate autocorrelation/effective sample size or block-bootstrap. Do not treat 20 closely spaced measurements as independent.
- Use paired analyses for shared initial conditions. For 30-cell prophet grids, use a preplanned regression (event rate, μ, interaction) and FDR/family-wise control, then confirm selected conditions on fresh seeds.
- Validate clustering/transition estimators on synthetic data with known no-transition, reversible, metastable, and first-order-like cases.

### 5. Reproducibility artifacts
For each run, write immutable:
- resolved config and all defaults;
- master seed plus derived RNG-stream seeds;
- git commit and dirty status;
- Python/OS/package lockfile, Modal image digest, hardware/runtime;
- exact script hash and command;
- full per-step or regular time series;
- per-γ measurements, convergence/autocorrelation diagnostics, terminal serialized state, and event logs;
- raw replicate tables in CSV/Parquet plus machine-readable analysis outputs.

Version figures from those tables in a one-command pipeline. Current requirements use lower bounds rather than exact versions (`requirements.txt:2-20`), and the headline writers overwrite fixed paths such as `sim/runs/hysteresis_sweep/hysteresis_data.json` (`sim/hysteresis_sweep.py:355-358`).

## Priority task list

1. **P0 — withdraw/relabel current hysteresis and lattice figures as exploratory.** They do not test carryover hysteresis.
2. **P0 — implement one shared experiment runner/state serializer**; eliminate the diverging inline kernels in hysteresis, finite-size, prophet, and lattice scripts.
3. **P0 — freeze an independent measurement layer** and run the coercion-mechanism ablation before making transition claims.
4. **P1 — execute the true paired carryover protocol** with convergence and rate/dwell sensitivity; save replicate-level data.
5. **P1 — redesign prophet study as a preregistered factorial intervention** with sustained escape and stratified controls.
6. **P1 — redo lattice comparison with calibrated metrics and paired seeds/states.**
7. **P2 — redo finite-size study with fixed parameters, expanded N, and formal scaling diagnostics.**
8. **P2 — replace smoke/asset tests** with invariants, deterministic replay tests, state-carryover tests, synthetic recovery tests, and tests that fail if figures lack raw provenance.
