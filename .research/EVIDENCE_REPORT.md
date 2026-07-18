# Canonical Evidence Cycle — Final Report

**Status:** completed exploratory evidence cycle  
**Scope:** canonical Python v2 kernel, contact-homophily coercion mechanism only  
**Interpretive limit:** these simulations do not prove a historical cause, a first-order transition, or a general theory of religion.

## 1. State-carrying schedule sensitivity

Each replicate initialized once at gamma 0, moved upward through gamma 1, then descended on the same kernel state. Clustering and fusion measurements were gamma-independent. Signed loop area is the trapezoidal integral of `descending dominance - ascending dominance`.

| Steps per gamma | Replicates | Mean signed area | 95% bootstrap CI | Assessment |
|---:|---:|---:|---:|---|
| 250 | 12 | -0.11660 | [-0.14870, -0.08353] | finite-rate path difference |
| 500 | 12 | -0.07383 | [-0.10606, -0.04089] | smaller finite-rate path difference |
| 1,000 | 12 | -0.00820 | [-0.05104, 0.03138] | interval includes zero |
| 2,000 | 1 | -0.02188 | not estimable with n=1 | descriptive only |

The path difference shrinks strongly as dwell increases and is not distinguishable from zero at 1,000 steps. Under this protocol, that pattern is more consistent with **finite-time lag** than robust equilibrium hysteresis. The single 2,000-step replicate is compatible with a small residual difference but cannot estimate uncertainty.

Two larger 2,000-step jobs (12 and 4 replicates) exceeded Modal's one-hour function timeout before artifacts were committed. This failure is documented rather than omitted.

## 2. Matched coercion ablation

Twelve replicates compared `null_gamma` against canonical `contact_homophily` from matching initial-state fingerprints at each requested gamma. Differences below are `contact_homophily dominance - null dominance`.

| Gamma | Mean paired difference | 95% bootstrap CI |
|---:|---:|---:|
| 0.0 | 0.0000 | [0.0000, 0.0000] |
| 0.1 | 0.1094 | [0.0560, 0.1628] |
| 0.2 | 0.0859 | [0.0391, 0.1354] |
| 0.3 | 0.0846 | [0.0365, 0.1380] |
| 0.4 | 0.0859 | [0.0339, 0.1432] |
| 0.5 | 0.0898 | [0.0208, 0.1602] |
| 0.6 | 0.0729 | [0.0065, 0.1354] |
| 0.7 | 0.1185 | [0.0703, 0.1719] |
| 0.8 | 0.0938 | [0.0299, 0.1589] |
| 0.9 | 0.0911 | [0.0378, 0.1510] |
| 1.0 | 0.1393 | [0.0807, 0.2031] |

In this finite matched-state simulation, contact homophily produces greater terminal belief-cluster dominance than the null condition. This is a mechanism-specific simulation contrast, not historical causal identification.

## 3. Claim decisions

- **Contact homophily increases concentration in this model:** supported for this finite 500-step ablation protocol.
- **Robust equilibrium hysteresis:** not supported by the completed dwell sensitivity; the loop contracts toward zero.
- **First-order phase transition:** not tested or established.
- **Historical explanation of monotheism:** not established; requires independent historical data and out-of-sample comparison.
- **Corpus validation/general theory:** not established by these experiments.

## 4. Modal runs

- Dwell 250: `ap-qTKySRmLqHWEUZ6PHqDnjW`
- Dwell 1,000: `ap-XFLlCNqSo9sdYgBVqxndPs`
- Dwell 2,000, 12 replicates, timed out: `ap-oVhrNLNWac2rMayeHCJqf8`
- Dwell 2,000, 4 replicates, timed out: `ap-HCGLn6xrOgoLhzAxV0I3Yt`
- Dwell 2,000, 1 replicate: `ap-ofeNiPI7Czik5vAxxJGuXa`
- Coercion ablation: `ap-paIBSp49kWeiuiCZMSZIc7`

All completed raw collections and deterministic analysis reports are retained under `.research/artifacts/`.
