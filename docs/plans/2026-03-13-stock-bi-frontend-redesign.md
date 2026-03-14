# Stock BI Frontend Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the Stock_BI frontend into a distinctive editorial trading-desk experience without breaking existing FastAPI endpoints or core interactions.

**Architecture:** Keep the current backend contract and most frontend state/chart logic intact. Replace the HTML shell and CSS system, then make small JavaScript adjustments so the existing data-loading, chart rendering, chat, and modal flows bind cleanly to the new layout.

**Tech Stack:** FastAPI static frontend, vanilla HTML/CSS/JS, ECharts, Python unittest smoke checks

### Task 1: Add a failing shell smoke test

**Files:**
- Create: `Stock_BI/codex/tests/test_frontend_shell.py`
- Modify: `Stock_BI/codex/frontend/index.html`

**Step 1: Write the failing test**

Assert that the redesigned shell contains the new editorial regions and command deck markers.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest Stock_BI.codex.tests.test_frontend_shell -v`
Expected: FAIL because the new layout markers are not present yet.

### Task 2: Rebuild the frontend shell

**Files:**
- Modify: `Stock_BI/codex/frontend/index.html`

**Step 1: Replace the top-level page structure**

Introduce an editorial hero, pulse rail, chart stage, and assistant command deck while preserving all DOM ids used by JavaScript.

**Step 2: Keep functional anchors stable**

Retain ids for charts, counters, chat, modal controls, update banner, consistency warning, and WebSocket status so existing JS can continue to work with minimal edits.

### Task 3: Replace the styling system

**Files:**
- Modify: `Stock_BI/codex/frontend/styles.css`

**Step 1: Define the new design language**

Add paper/ink/trading color tokens, layered background treatments, expressive typography, responsive editorial grid, and modal/table styling.

**Step 2: Restyle all interactive surfaces**

Refresh overview cards, chart controls, quick commands, chat bubbles, banners, and modal layouts so the UI is coherent across desktop and mobile.

### Task 4: Make minimal JavaScript compatibility updates

**Files:**
- Modify: `Stock_BI/codex/frontend/app.js`

**Step 1: Update selectors or small UI hooks only where needed**

Keep data flow intact. Only adapt code where the new shell needs extra labels, summary text, or safe DOM handling.

**Step 2: Preserve behavior**

Ensure chart toggles, quick commands, chat interactions, stock modal, industry modal, WebSocket updates, and banners still work.

### Task 5: Verify

**Files:**
- Verify: `Stock_BI/codex/frontend/index.html`
- Verify: `Stock_BI/codex/frontend/styles.css`
- Verify: `Stock_BI/codex/frontend/app.js`
- Verify: `Stock_BI/codex/tests/test_frontend_shell.py`

**Step 1: Run the smoke test**

Run: `python3 -m unittest Stock_BI.codex.tests.test_frontend_shell -v`
Expected: PASS

**Step 2: Run a backend syntax check**

Run: `python -m py_compile Stock_BI/codex/backend/main.py Stock_BI/codex/frontend/../backend/routers/market.py`
Expected: PASS

**Step 3: Review the diff**

Run: `git diff -- Stock_BI/codex/frontend/index.html Stock_BI/codex/frontend/styles.css Stock_BI/codex/frontend/app.js Stock_BI/codex/tests/test_frontend_shell.py docs/plans/2026-03-13-stock-bi-frontend-redesign.md`
Expected: Only the planned redesign and test changes appear.
