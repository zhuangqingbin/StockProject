# Stock BI Editorial Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reframe `apps/stock_bi/codex/frontend` as a sharper editorial-style market desk without changing the existing data contract.

**Architecture:** Keep the current React Query and Zustand flow intact, and concentrate the refactor in presentation components plus global styles. Introduce a ticker-style market strip and a stronger information hierarchy in the shell while preserving existing drawers and chart fetch behavior.

**Tech Stack:** React 18, TypeScript, Vite, Vitest, Testing Library, Zustand, TanStack Query, ECharts

### Task 1: Lock the new interaction and content structure with tests

**Files:**
- Create: `apps/stock_bi/codex/frontend/src/test/features/chat-console/ChatConsole.test.tsx`
- Create: `apps/stock_bi/codex/frontend/src/test/features/market-overview/HeroBrief.test.tsx`
- Modify: `apps/stock_bi/codex/frontend/package.json`

**Step 1: Write the failing tests**

- `ChatConsole.test.tsx`
  - Verify the textarea accepts typing without auto-submitting.
  - Verify `Enter` sends the draft and `Shift+Enter` keeps multiline editing.
- `HeroBrief.test.tsx`
  - Verify the hero renders the new editorial section labels, lead number, and focus copy from summary data.

**Step 2: Run tests to verify they fail**

Run:

```bash
npm test -- src/test/features/chat-console/ChatConsole.test.tsx src/test/features/market-overview/HeroBrief.test.tsx
```

Expected:
- `ChatConsole` fails because the current key handling blocks normal typing.
- `HeroBrief` fails because the new editorial copy and structure do not exist yet.

**Step 3: Add the minimal implementation**

- Update `ChatConsole.tsx` keyboard handling so only bare `Enter` submits.
- Update `HeroBrief.tsx` render structure and copy helpers to match the new content model.

**Step 4: Re-run the focused tests**

Run:

```bash
npm test -- src/test/features/chat-console/ChatConsole.test.tsx src/test/features/market-overview/HeroBrief.test.tsx
```

Expected: PASS

### Task 2: Recompose the page into an editorial market desk

**Files:**
- Create: `apps/stock_bi/codex/frontend/src/features/market-overview/MarketTape.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/features/market-overview/MarketShell.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/features/market-overview/MarketHeader.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/features/market-overview/HeroBrief.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/features/market-overview/OverviewCards.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/features/market-overview/IndexPulse.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/features/chart-stage/ChartStage.tsx`
- Modify: `apps/stock_bi/codex/frontend/src/features/chat-console/ChatConsole.tsx`

**Step 1: Insert the new top-level information hierarchy**

- Header becomes a desk masthead with trade date, websocket status, and refresh CTA.
- Add a ticker strip fed by summary data and major indices.
- Make the hero the primary narrative block and reposition the pulse board as a supporting column.

**Step 2: Update supporting components**

- Convert overview cards into a tighter ledger layout.
- Reframe chart stage and chat console titles/copy to fit the editorial concept.
- Keep drawers, queries, and state wiring unchanged.

**Step 3: Keep responsive behavior intact**

- Maintain a readable single-column collapse under tablet widths.
- Preserve accessible headings, buttons, and section labels.

### Task 3: Replace the visual system

**Files:**
- Modify: `apps/stock_bi/codex/frontend/src/styles/app.css`

**Step 1: Replace the dark glass system**

- Introduce a paper-toned theme with ink typography and restrained red/green signal colors.
- Add a grain/grid background and ticker motion that suit a market desk.

**Step 2: Restyle shared primitives**

- Update buttons, badges, surfaces, tables, drawers, and form controls to match the new system.
- Preserve component API shape so no calling code changes outside styles and local markup.

**Step 3: Audit responsive states**

- Ensure the masthead, hero, tape, chart stage, and chat console scale cleanly on tablet and mobile.

### Task 4: Verify the refactor

**Files:**
- No code changes expected

**Step 1: Run the frontend test suite**

Run:

```bash
npm test
```

Expected: PASS

**Step 2: Run the production build**

Run:

```bash
npm run build
```

Expected: PASS

**Step 3: Review the diff**

Run:

```bash
git diff -- apps/stock_bi/codex/frontend docs/plans/2026-03-15-stock-bi-editorial-refactor.md
```

Expected: only the planned frontend refactor and plan file changes
