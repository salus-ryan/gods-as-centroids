# Claim Ledger — Baseline Audit

**Baseline:** `268af3c5c9ffcbb3e0f54e67f63f4e83a8f0f493`  
**Archive tag:** `legacy-baseline-268af3c`  
**Purpose:** classify claims before modifying the research model. Statuses describe the baseline only.

| ID | Baseline claim | Primary location | Evidence type | Baseline status | Required disposition |
|---|---|---|---|---|---|
| C-01 | Deities/godforms can be represented as prestige-weighted centroids of belief clusters. | Paper §§2.4, 3 | Formal framing + implementation | Supported as a definition/modeling choice | Retain as a conditional modeling thesis. |
| C-02 | Coercion produces polytheism-to-monotheism collapse. | Paper §§4.1–4.3 | Simulation | Exploratory; outcome partly encoded by clustering/merge thresholds. | Rebuild with independently motivated mechanisms and ablations. |
| C-03 | The transition is first-order. | Paper §4 | Simulation interpretation | Unsupported. | Remove unless predeclared finite-size and discontinuity evidence supports it. |
| C-04 | The system exhibits hysteresis with Δγ≈0.55. | Paper §4.4 | Modal sweep | Unsupported; reverse sweep initializes a fresh high-γ system. | Reimplement a continuous state-carrying forward/reverse protocol. |
| C-05 | Hamming centroids require 9× less coercion. | Paper §4.5 | Separate simulation | Exploratory. | Reproduce from canonical model and compare matched parameters. |
| C-06 | Ritual stabilizes centroid dynamics. | Paper §5.2 | Smoke-level simulation test | Exploratory. | Define outcome and effect criterion; run seeded multi-run experiment. |
| C-07 | Prestige concentration speeds convergence. | Paper §5.3 | Smoke-level simulation test | Exploratory. | Test via ablation and report uncertainty. |
| C-08 | Sensory-restricted agents converge to the same attractors. | Paper §5.1 | Simulation | Unsupported; current test compares mostly cluster counts. | Rebuild observation model and test matched centroids/beliefs. |
| C-09 | Parameters are corpus-calibrated. | README, Paper §8, calibration script | LLM-assisted text scores | Supported only as exploratory annotation-based calibration. | Rename and document as LLM-assisted semantic annotation/calibration. |
| C-10 | Model is validated against 5,000 years of history/Seshat. | Paper abstract, historical sections | Narrative schedule + simulation | Unsupported. | Remove or add actual imported data, held-out tests, and explicit estimators. |
| C-11 | Four LLMs have Krippendorff's α=0.903. | README, Paper §8 | Saved scorer output | Needs independent audit of data/prompt/calculation. | Retain only with reproducible scorer inputs and calculation artifact. |
| C-12 | Model generalizes to politics/personality. | README | Separate LLM/embedding demo | Exploratory extension, not validation of religion model. | Move to appendix/future work unless independently evaluated. |

## Release rule

No claim may be described as validated, causal, historical explanation, first-order, or hysteretic until its acceptance test, raw artifacts, exact configuration, and canonical-model revision are recorded in `docs/CLAIM_LEDGER.md`.
