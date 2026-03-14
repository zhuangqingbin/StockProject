# Monorepo Reorganization Design

## Goal

Reorganize this repository into a clear monorepo with two long-term maintained projects:

- `apps/stock_data_platform`: the current stock data fetching and analysis codebase
- `apps/stock_bi`: the existing `Stock_BI` application

Everything else should be explicitly categorized as either experiments, archived assets, or documentation so the root of the repository becomes understandable and maintainable.

## Current Problems

The repository is in a half-migrated state:

- The current root entrypoint still imports removed modules.
- The README documents an old structure that no longer matches the code.
- Secrets are committed in source files.
- Reusable stock data code lives beside notebooks, screenshots, PDFs, and unrelated side projects.
- The `common/` module mixes unrelated concerns such as database connection helpers, finance math, AkShare access, and Backtrader runtime classes.
- `DataFetch/` already has a cleaner base class and client wrapper, but the rest of the project has not been aligned around that direction.

## Target Structure

The repository should converge toward this shape:

```text
.
|-- apps/
|   |-- stock_data_platform/
|   `-- stock_bi/
|-- shared/
|   `-- stock_core/
|-- experiments/
|-- assets/
|-- docs/
|-- DataStore/
|-- README.md
`-- pyproject.toml or requirements files
```

Notes:

- `DataStore/` stays at the repo root because both maintained projects may need local data.
- `shared/stock_core/` only contains stable reusable code such as config loading, path helpers, database connection factories, and shared stock data clients.
- `experiments/` holds notebooks, backtesting examples, side prototypes, and historical explorations.
- `assets/` holds PDFs, screenshots, generated images, and other non-code artifacts.

## Project Boundaries

### `apps/stock_data_platform`

This project owns:

- TuShare and related market data access
- local data persistence helpers
- analysis scripts that are not BI-specific
- CLI and sample workflows

It should not own:

- BI-specific APIs, frontend code, or websocket chat behavior

### `apps/stock_bi`

This project owns:

- frontend and backend application code under the current `Stock_BI/codex`
- application-specific tests and deployment scripts

### `shared/stock_core`

This package should initially hold only stable, reusable infrastructure:

- `TuShareClient`
- `BaseDataFetch`
- config parsing and environment variable loading
- database engine factory
- path helpers and lightweight date/code utilities

It should not absorb BI routers, notebook-only helpers, or prototype code.

## Migration Strategy

The migration should happen in controlled passes rather than a single large move:

1. Fix critical correctness and security issues first.
2. Create the target directory scaffolding.
3. Move maintained projects into `apps/`.
4. Move experiments and assets into dedicated areas.
5. Update imports, entrypoints, and documentation.
6. Extract reusable code into `shared/stock_core` only after the boundaries are stable.

This order avoids mixing functional fixes with large path changes too early.

## Immediate Refactor Priorities

The first pass should focus on high-value, low-regret changes:

1. Remove hard-coded secrets from source.
2. Replace broken root entrypoints with working, documented ones.
3. Refresh the root README so it matches the real repository.
4. Introduce directory boundaries for maintained apps, experiments, and assets.
5. Clean up the worst `common/utils.py` coupling and missing imports.

## Verification Strategy

Verification should be lightweight but explicit:

- run existing automated tests where available
- run import smoke checks for `DataFetch`
- run a root-level structural check to ensure moved directories are discoverable
- document any pre-existing test failures separately from migration regressions

## Non-Goals For The First Pass

The first pass should not attempt:

- a full packaging overhaul for every subproject
- complete notebook cleanup
- rewriting every fetcher into a declarative registry
- deleting historical content unless it is clearly disposable

Those are follow-up phases once the repository boundaries are stable.
