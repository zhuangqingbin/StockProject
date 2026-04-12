# Repo Governance Design: Dual-Project Monorepo

## Context

This repository currently contains two real projects under `apps/`:

- `apps/data_hub`: A-share data ingestion, persistence, scheduling, data exploration, and monitoring.
- `apps/quant_platform`: Quant research, strategy backtesting, visualization, and application APIs.

They are related, but they are not one system split across folders. The intended dependency direction is:

`quant_platform -> data_hub data outputs`

`quant_platform` may consume data managed by `data_hub`, but it is not a submodule of `data_hub`, and `data_hub` must not depend on `quant_platform`.

The repo also contains `shared/stock_core`, which already provides a small amount of repository-level infrastructure such as env loading, DB URL helpers, and Python runtime resolution.

## Problem Statement

The current repo narrative is still too easy to misread:

- It is not obvious from the repo entrypoints that there are two independent projects.
- The boundary between repo-level docs and project-level docs is not explicit.
- `shared/` has useful infrastructure code, but its allowed scope is not written down.
- Generated artifacts and source-of-truth files are not consistently separated in documentation and repo hygiene.
- Review feedback can turn into stack-unification work unless the intended project relationship is made explicit first.

## Goals

- Define the repository as a monorepo containing two independent projects and one minimal shared infrastructure layer.
- Make project boundaries, dependency direction, and ownership rules explicit.
- Clarify where documentation should live and what counts as source of truth.
- Improve repo entrypoints so a new contributor can quickly understand what each project does and how to run it.
- Establish a minimal engineering baseline without forcing technology-stack unification.

## Non-Goals

- Unifying the frontend stacks, backend stacks, or test frameworks across the two projects.
- Merging `data_hub` and `quant_platform` into one application.
- Moving project business logic into `shared/`.
- Rewriting the projects to share one run script, one build system, or one release process.

## Target Repository Model

The repository should be treated as:

- `apps/data_hub`: Data production and observability project
- `apps/quant_platform`: Data consumption and research application project
- `shared/`: Minimal repo-wide technical infrastructure
- `docs/`: Repo-level design, governance, and cross-project documents
- `experiments/`: Exploratory work, not a source of truth

## Boundary Definitions

### `apps/data_hub`

Responsibilities:

- Collect market and reference data
- Persist canonical operational datasets
- Run schedules, backfills, and infrastructure sync
- Provide read-only exploration and monitoring for managed datasets

Out of scope:

- Quant strategy research workflows
- Research report serving as a primary product concern
- Application features that belong to `quant_platform`

### `apps/quant_platform`

Responsibilities:

- Use market datasets to support research, analysis, visualization, and strategy workflows
- Expose application APIs and UI for quant use cases
- Maintain its own app logic, research workflows, and project docs

Out of scope:

- Owning `data_hub` scheduling or ingestion logic
- Becoming the orchestration surface for `data_hub`

### `shared/stock_core`

Allowed:

- Env discovery and loading
- DB connection and URL helpers
- Python runtime discovery
- Small repo-level utility code with no project business semantics

Not allowed:

- `data_hub` business models, fetcher logic, or scheduler behavior
- `quant_platform` strategy, research, or API business logic
- Shared abstractions created only to force superficial consistency between the projects

## Directory and Documentation Rules

### Directory Ownership

- `apps/data_hub/**` belongs to the `data_hub` project
- `apps/quant_platform/**` belongs to the `quant_platform` project
- `shared/**` belongs to repo-wide technical infrastructure
- `docs/**` is reserved for repo-level documents
- `experiments/**` is exploratory and non-canonical

### Documentation Ownership

Repo-level documents belong in `docs/` when they describe:

- Repository governance
- Cross-project dependency rules
- Repo-wide migration or upgrade plans
- Shared infrastructure conventions

Project-level documents belong in each project when they describe:

- Internal architecture
- APIs, jobs, scripts, workflows, or operations
- Project-specific requirements and plans

Implication:

`docs/` must not become a general dump for project-internal design notes when those notes only affect one project.

### README Layering

- Root `README.md` explains the monorepo layout, names both projects, explains their relationship, and links to each project entrypoint.
- `apps/data_hub/README.md` explains only `data_hub`, while noting that `quant_platform` may consume its managed data.
- `apps/quant_platform/README.md` explains only `quant_platform`, while noting that some research workflows rely on data sourced from `data_hub`-managed datasets.

## Engineering Baseline Rules

### Commands

- The repo root should provide discovery, not orchestration.
- Each project remains responsible for its own run, test, and init scripts.
- Do not introduce a fake unified root script for both projects.

### Tests

- The root documentation should index project-specific test commands.
- Each project README remains the source of truth for its own test workflow.
- Test framework differences are acceptable.

### Environment Variables

Environment variables should be documented in three groups:

- Repo-shared infra variables
- `data_hub` project variables
- `quant_platform` project variables

The goal is clarity of ownership, not merging configuration surfaces.

### Generated Artifacts

Default rule:

Reproducible generated artifacts should not be committed unless there is an explicit reason to version them.

This applies to directories such as:

- `node_modules/`
- `dist/`
- `.cache/`
- `.pytest_cache/`
- research output directories unless specifically designated as versioned deliverables

### Source of Truth

Canonical source of truth should be:

- Source code under `apps/**` and `shared/**`
- Maintained project READMEs
- Repo-level docs under `docs/` only when they truly apply across projects

Non-canonical supporting material:

- `experiments/**`
- Generated outputs
- Ad hoc local notes or copied files

## Acceptance Criteria

The repo governance pass is complete when:

1. The root README accurately presents the repo as two independent projects plus a shared infrastructure layer.
2. `data_hub` and `quant_platform` READMEs both clearly state their scope and relationship.
3. `shared/stock_core` usage boundaries are documented.
4. Repo-level vs project-level documentation placement is explicitly defined.
5. Generated artifact policy and source-of-truth rules are documented.

## Refactor Plan: Dual-Project Repository Governance

### Current State

The repository already has two meaningful application areas, but the boundary is mostly inferred from code and partial README content. Repo-level narrative still leans toward `data_hub` as the center of the repository, while `quant_platform` has grown into a separate project that consumes related data. Documentation location rules and generated-artifact expectations are not yet formalized.

### Target State

The repository reads clearly as a monorepo with two independent projects and a minimal shared infra layer. New contributors can identify project roles, dependency direction, commands, docs, and source-of-truth locations without reading code first.

### Affected Files

| File | Change Type | Dependencies |
|------|-------------|--------------|
| `README.md` | modify | depends on final repo narrative |
| `apps/data_hub/README.md` | modify | depends on boundary wording |
| `apps/quant_platform/README.md` | modify | depends on boundary wording |
| `docs/README.md` or `docs/repo-governance.md` | create | depends on approved governance rules |
| `.gitignore` | modify | depends on artifact policy decisions |
| project-specific docs under `apps/data_hub/**` and `apps/quant_platform/**` | selective modify/move | depends on doc ownership rules |

### Execution Plan

#### Phase 1: Boundary and Narrative

- [ ] Step 1.1: Update the root `README.md` to describe the repo as two independent projects and one shared infra layer.
- [ ] Verify: A reader can identify project roles and the dependency direction from the first screen of the README.
- [ ] Step 1.2: Update `apps/data_hub/README.md` to describe `data_hub` scope without treating `quant_platform` as part of it.
- [ ] Verify: The README defines `data_hub` responsibilities and mentions `quant_platform` only as a downstream consumer.
- [ ] Step 1.3: Update `apps/quant_platform/README.md` to explicitly describe its dependency on `data_hub`-managed data without implying code-level coupling.
- [ ] Verify: The README explains what data it expects and what it does not own.

#### Phase 2: Documentation Placement

- [ ] Step 2.1: Create one repo-level governance document under `docs/` defining ownership rules for `apps/`, `shared/`, `docs/`, and `experiments/`.
- [ ] Verify: The document distinguishes repo-level vs project-level docs with examples.
- [ ] Step 2.2: Audit root `docs/` entries and identify project-specific docs that should remain project-local in future iterations.
- [ ] Verify: A short inventory exists classifying docs as repo-level or project-level.

#### Phase 3: Engineering Baseline

- [ ] Step 3.1: Add or update documentation for repo-shared vs project-specific environment variables.
- [ ] Verify: Variables are grouped by ownership, not mixed in one undifferentiated list.
- [ ] Step 3.2: Update `.gitignore` and related docs for generated artifact handling, especially research outputs and local workspace noise.
- [ ] Verify: Reproducible local artifacts are excluded unless deliberately versioned.
- [ ] Step 3.3: Add a compact root-level command index pointing to each project's run/test/init commands.
- [ ] Verify: A new contributor can find the correct commands without searching subdirectories first.

#### Phase 4: Drift Cleanup

- [ ] Step 4.1: Correct documentation drift such as outdated test counts, stale commands, or old repo descriptions.
- [ ] Verify: Spot-check project READMEs against current commands and test layout.
- [ ] Step 4.2: Remove or clearly mark ambiguous non-canonical files when they risk being mistaken for official docs.
- [ ] Verify: There is no obvious alternative "entry README" or copied repo summary file competing with the real source of truth.

### Rollback Plan

If something fails:

1. Revert only the repo-governance documentation files first.
2. Revert README wording changes separately from `.gitignore` changes.
3. Keep project code untouched during this pass so rollback remains documentation-only.

### Risks

- The repo narrative may over-correct and make the projects seem more isolated than they are. Mitigation: state the data dependency explicitly.
- Generated artifact policy may accidentally hide files some workflows currently rely on. Mitigation: confirm versioned-output expectations before tightening ignore rules.
- Project-level docs may still drift if ownership is written once but not followed. Mitigation: keep the governance rules short and visible from the root README.
