# Research Orchestration

Parallel Pi agents operate only in isolated Git worktrees. They never push or merge.

## Roles

| Role | Worktree branch | Write scope |
|---|---|---|
| Model | `research/model-*` | canonical-kernel code and unit tests only |
| Methods | `research/methods-*` | experiment runner, configs, analysis tests only |
| Evidence | `research/evidence-*` | paper/README/data-card materials only |
| Integrator | `research/rebuild-v2` | review, conflict resolution, test execution, merge commits |

## Rules

1. Every task names allowed paths, forbidden paths, acceptance tests, and a commit requirement.
2. Agents first inspect and report; implementation begins only from an accepted specification.
3. No agent edits generated figures, saved legacy results, or another role's paths.
4. Every change is reviewed against `.research/CLAIM_LEDGER.md` and `MODEL_V2_SPEC.md`.
5. Integration is serial: inspect diff, run targeted tests, then merge/cherry-pick.
6. Raw agent reports are retained under `.research/artifacts/subagent-audits/`; process stderr and local worktrees are ignored.

## Baseline parallel audit

Three read-only Pi subagents ran at baseline `a3488c3`:

- `model.md` — model mechanics;
- `methods.md` — experiments and statistics;
- `evidence.md` — corpus and scholarly claims.

Their findings are inputs to the v2 specification, not external validation.
