# Repository Governance

## Repository Model

This repository contains:

- `apps/data_hub`: data production and observability
- `apps/quant_platform`: quant research and application workflows
- `shared/stock_core`: minimal shared technical infrastructure

## Dependency Direction

- `quant_platform` may consume datasets managed by `data_hub`
- `data_hub` must not depend on `quant_platform`
- shared infrastructure must remain business-neutral

## Documentation Placement

Use `docs/` for:

- repo governance
- cross-project rules
- repo-wide upgrade and migration plans

Use project-local docs for:

- internal architecture
- project-specific scripts and operations
- project-specific requirements and plans

## Source of Truth

Canonical:

- source code under `apps/**` and `shared/**`
- maintained project READMEs
- repo-level governance docs under `docs/`

Non-canonical:

- `experiments/**`
- generated outputs
- copied notes or temporary summaries

## Generated Artifacts

Default rule:

Do not commit reproducible generated artifacts unless there is an explicit reason to version them.

Examples in this repository include:

- `node_modules/`
- `dist/`
- `.cache/`
- `.pytest_cache/`
- `.codex-runlogs/`
- `.omc/sessions/`
- `.omc/state/`
- `apps/quant_platform/research/output/`
