## Evidence audit

### Bottom line
The repository contains **simulation outputs, LLM-assisted annotations, hand-authored scenarios/priors, and synthetic ML demonstrations**. It contains **no direct human-subject evidence, no imported/versioned historical dataset, and no validated historical backtest**. The paper repeatedly upgrades these materials into empirical and causal claims.

### Claim ledger

| Claim | Actual evidence | Audit finding / replacement |
|---|---|---|
| Godforms are prestige-weighted centroids | Formal definition plus implemented clustering | **Modeling choice, not empirical finding.** Retain as: “We define godforms as prestige-weighted cluster centroids in this model.” |
| Coercion causes polytheism→monotheism | Simulation, but coercion directly widens assignment and merge thresholds (`sim/swarm_kernel.py:521-566`) | **Outcome-coupled simulation mechanism.** Replace “coercion drives” with “In this parameterization, increasing γ changes clustering/merging rules and is associated with fewer clusters.” |
| First-order phase transition | Simulation interpretation | **Unsupported.** No finite-size scaling, discontinuity analysis, coexistence test, or pre-registered criterion. Replace with “a sharp transition-like change in this finite simulation.” Remove “first-order.” |
| Hysteresis, Δγ≈0.55 | Saved aggregate simulation output; not raw runs (`sim/runs/hysteresis_sweep/hysteresis_data.json:1`) | **Invalid protocol.** `do_sweep` creates a new kernel for reverse direction with a new seed (`sim/hysteresis_modal.py:367-386`), rather than reversing the forward terminal state. Replace with “Separate upward- and downward-initialized sweeps differed under this MiniKernel; this is not evidence of hysteresis.” |
| Hamming lattice needs 9× less coercion | Separate hand-authored/inline lattice simulation | **Exploratory simulation only.** The lattice implementation is not the canonical kernel and includes a fixed `momentum=False` encoding (`sim/lattice_hysteresis_modal.py:145-160`). Replace “requires” with “in this matched-but-separate implementation, the selected threshold criterion occurred at a lower γ.” |
| Accessibility corollary | Simulation; partly hand-authored sensory mappings | **Unsupported as stated.** The experiment calls `kernel.transmit()` rather than `step()` (`sim/experiments/accessibility_experiment.py:125`), so interaction, restriction, clustering, and measurement dynamics are not executed. Canonical interaction also computes a restricted context but scores against full context. Replace with “a proposed, testable hypothesis; no valid simulation or human evidence is reported.” |
| Ritual reduces drift 40% | Intended simulation | **No valid reported reproduction.** The script likewise calls only `transmit()` (`sim/experiments/corollary2_ritual.py:86`); it cannot generate the claimed centroid trajectory. Replace with “unvalidated simulation hypothesis.” |
| Prestige amplification speeds convergence | Intended simulation | **No valid reported reproduction.** It calls only `transmit()` (`sim/experiments/corollary3_prestige.py:49`). Replace with “unvalidated simulation hypothesis.” |
| Prophet/mutation “Second Axial Age” sweet spot | Separate inline MiniKernel simulation | **Exploratory scenario simulation.** Saved results show escape even at prophet rate 0 and mutation .05 (`sim/runs/prophet_escape/prophet_escape_data.json:1-18`), contradicting the paper’s claim that prophets are required. Replace with “Under one inline model and outcome definition, parameter combinations produced differing escape frequencies.” |
| 12 axes are grounded in comparative religion | Hand-authored ontology, literature-informed | **Conceptual framing, not validated measurement model.** The paper itself concedes the space is hand-crafted (`paper/gods_as_centroids_v2.md:619`). Say “literature-informed, author-specified axes.” |
| 12 deity priors / named deity results | Hand-authored vectors | **Synthetic inputs.** The paper’s 16-prior bottleneck experiment explicitly uses “500 noisy samples each” (`paper/gods_as_centroids_v2.md:300-304`). Say “synthetic noisy samples around author-specified priors,” not deity data. |
| Braille preservation, classification, capacity results A–E | Autoencoder trained/evaluated on synthetic priors and augmented versions | **Synthetic ML evidence only; not theological validity.** Replace “preserves theology” with “reconstructs and classifies synthetic vectors generated around the supplied priors.” |
| LLM judge says 8/8 semantic equivalence | Claude-generated profiles judged by GPT-4o-mini | **LLM-assisted evaluation of LLM-generated material, not independent validation** (`paper/gods_as_centroids_v2.md:335`). Replace “confirms” with “an LLM judge rated all eight generated profile pairs equivalent; this is an automated face-validity check.” |
| “Real embeddings” / text structure | 24 selected passages scored by Claude | **LLM-assisted annotation of genuine texts.** Texts are genuine source material, but coordinates are model judgments, not human-coded or observed beliefs (`paper/gods_as_centroids_v2.md:337`). Replace “real embeddings” with “Claude-generated axis scores for selected passages.” |
| Four-LLM α=.903 | Saved LLM outputs and computational summary | **Genuine computational agreement measurement of four model outputs, conditional on artifacts.** But it is not Krippendorff’s standard estimator: code calls it a “simplified ordinal” ratio approximation (`mlx-pipeline/multi_scorer.py:300-326`). Replace “Krippendorff’s α=.903” with “a repository-defined variance-ratio agreement statistic of .903; standard Krippendorff α remains to be calculated.” |
| Corpus-calibrated parameters | LLM-scored selected texts plus heuristic transforms | **LLM-assisted, assumption-laden calibration—not empirical parameter estimation.** μ is transformed with a fixed 0.35 denominator and clamped (`sim/corpus_calibration.py`, `estimate_mutation_rate`); fission labels are author-selected historical categories. Replace “empirically calibrated” with “heuristically derived from LLM-scored corpus dispersion.” |
| Seshat-derived coercion schedule | Hand-authored dated γ schedule | **Hand-authored historical scenario.** `estimate_coercion_schedule()` embeds the values directly (`sim/corpus_calibration.py:230-298`); no Seshat import occurs. Replace “Seshat-derived” with “author-specified historical scenario informed by stated historical interpretations.” |
| 5,000-year historical validation, r=.82 | Hand-authored N_eff values, hand-authored γ/event schedule, simulation | **Unsupported/circular.** Historical values and causal inputs co-reside in `HISTORICAL_EPOCHS` (`sim/experiments/backtesting.py:32-56`); prophet dates are also scheduled (`:62-100`), and the script calls `transmit()` rather than `step()` (`:100`). Replace with “an illustrative historical narrative scenario; no empirical backtest is currently reported.” Remove r/p claims. |
| 826 passages / 37 traditions | Real public text excerpts plus original selected passages; LLM scores | **Mixed provenance.** `scraped_passages.json` records 770 passages and radically unequal coverage—many traditions have 3 passages while 14 have 50 (`lattice_autoencoder/data/scraped_passages.json:1-45`). Say “a convenience corpus of 826 passages with uneven coverage,” not “canonical” or globally representative. |
| MMLA 100% classification / 87.1% agreement | ML experiment with label supervision and synthetic scorer variants | **In-sample/augmentation result, not corpus validation.** Train and validation loaders derive from the same passages (`lattice_autoencoder/train_modal.py:218-219`); “four scorers” are simulated by adding noise to consensus scores (`:614-626`). Replace “perfect tradition discrimination” with “held-out augmented instances of the same passages were classified perfectly; no source-, passage-, or tradition-held-out evaluation was performed.” |
| Operator prediction 42.9% | Hand-labeled pairs from family/schism lists | **Hand-authored scenario labels, not historical outcomes.** Do not call it prediction of fusion/fission/prophecy. Say “classification of rules used to construct synthetic pair labels.” |
| Politics/personality 88/90% | Hand-authored ideology/personality prototypes + Gaussian noise | **Synthetic demonstration.** Priors are embedded in source (`mlx-pipeline/non_theological_demo.py:43-78`) and samples are generated around them. Replace “generalizes” with “works on two additional author-specified synthetic vector datasets.” |
| AGI / universal semantic substrate / Worldform | LLM self-scoring, majority-voting, interpretive prose | **Speculative extension; LLM-assisted demonstration.** Move from results/conclusion to “Speculation and future work.” |

## Material classification

- **Genuine empirical materials:** religious text excerpts and cited external scholarship, subject to source/translation/licensing verification. They are inputs, not measurements of human belief or religious history.
- **LLM-assisted annotation:** all 12-axis passage scores, consensus embeddings, LLM judge results, and live braiding outputs. Prompt defines the construct being measured (`mlx-pipeline/multi_scorer.py:72-104`).
- **Hand-authored scenarios/labels:** axes, deity priors, expected corpus clusters (`mlx-pipeline/corpus_parts/part1_abrahamic.py:8-33`), schism categories, historical N_eff, γ schedule, prophet dates, political/personality priors.
- **Simulations:** ABM sweeps, lattice sweeps, prophet escape, ritual/prestige/accessibility experiments.
- **Synthetic ML:** noisy deity-prior autoencoders; political/personality demonstrations; MMLA’s simulated per-model scorer vectors.

## Required data card / provenance work

1. **Corpus card:** exact text, source URL/edition, translator, language, copyright/license, retrieval date, immutable hash, passage boundaries, selection rule, exclusions, tradition/community review, and counts by tradition/source/time period.
2. **Annotation card:** prompt/version, provider model ID and dated snapshot, temperature and all API parameters, raw completions, parse failures/retries/zero substitutions, request IDs, costs, scorer order, normalization, and known construct-validity limitations.
3. **Historical-data card:** replace embedded epochs with versioned source tables; define geography, population denominator, “tradition,” and N_eff estimator; record extraction and missing-data rules. Separate outcome data from γ construction.
4. **Experiment card per figure:** canonical commit hash, config, seeds, raw replicate-level records, hardware/software/dependencies, exclusions, summary code, and figure hash. Current hysteresis JSON contains aggregates rather than raw runs.
5. **Ethics/representation statement:** explain that traditions are heterogeneous and texts are not proxies for adherents; obtain domain-expert/community review before comparative claims.

## Priority remediation

**P0 — retract/reword before dissemination**
1. Remove “validated against 5,000 years,” r=.82/p-value, Seshat-derived schedule, first-order transition, hysteresis, causal historical explanations, and prophet-necessity claims.
2. Correct README’s headline claims and result table (`README.md:8-21,165`).
3. Mark all autoencoder, cross-domain, and AGI claims as synthetic or speculative.

**P1 — make simulations interpretable**
4. Use one canonical kernel for every experiment; eliminate inline MiniKernels.
5. Implement a state-carrying forward→reverse protocol; retain raw trajectories; predefine threshold and hysteresis acceptance tests.
6. Decouple γ from cluster/merge geometry; specify a social enforcement mechanism and run ablations.
7. Repair corollary/backtest scripts to call `step()`, then rerun with raw replicate outputs and uncertainty intervals.
8. Fix seeded reproducibility: sensory noise uses module-global `random.gauss` (`sim/swarm_kernel.py:276`).

**P2 — make corpus/ML claims auditable**
9. Publish the data/annotation cards and raw scorer artifacts; calculate standard Krippendorff α with a stated level/metric.
10. Use independent human annotation and adjudication for construct validation.
11. Evaluate MMLA with passage-, source-, and tradition-held-out splits; do not synthesize scorer replicates from consensus.
12. Add tests for scientific acceptance criteria. Existing tests explicitly describe themselves as smoke tests and mostly verify files/qualitative behavior (`tests/test_paper_claims.py:1-9,291-362`).
