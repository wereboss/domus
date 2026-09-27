# Domus - Your Home, Organised 🏡

Domus is an offline-first Progressive Web App (PWA) designed for parents to manage household logistics and finances with low cognitive friction and high situational durability.

---

## Architecture Foundation (Phase 1 Baseline)

- **Database Layer (Option A: Dual SQLite WAL):**
  - `data/logistics.db`: Household members, tasks, chores, notes.
  - `data/finance.db`: Daily ledger expenses, recurring fixed bills.
  - Physically decoupled database engines with SQLite WAL mode enabled.
- **Backend Orchestrator:** FastAPI asynchronous API core.
- **Frontend App Shell:** Single-Page PWA built with HTML5, Pico.css, Alpine.js, and Dexie.js (IndexedDB).
- **Authentication:** Lightweight 4-digit PIN authentication per household member with persistent device sessions and instant profile switching.
- **Unified Timeline:** In-memory chronological aggregator interleaving overdue tasks, due bills, timed events, and daily chores into a single glanceable feed.

---

## UX Directives Compliance

1. **One-Handed Thumb Layout:**
   - 5 core views anchored to the bottom 68px bar (`Today`, `Inbox`, `Logistics`, `Finances`, `Family`).
   - Center Floating Action Button (`+`) triggers a thumb-accessible Bottom Sheet Drawer.
   - Large 48×48px minimum touch targets for checkboxes and triage approvals.
2. **Zero-Friction Ingestion:**
   - Add a task or ledger expense in under 3 taps from idle.
3. **Glanceable & Low Cognitive Load:**
   - 3-question dashboard metric header: Tasks Done, Bills Due, Spent Today.
   - Clean context stripping and semantic tags.
4. **Optimistic & Resilient UI (Zero-Network Anxiety):**
   - Offline-first cache powered by `Dexie.js` and `sw.js`.
   - Subtle `"⚡ Offline"` indicator pill without disruptive modals.
   - Optimistic local checkbox toggling.
5. **Multi-Sensory & Performance Restraint:**
   - Native system typography.
   - Strict semantic color standard: Green (`#10b981`), Amber (`#f59e0b`), Red (`#ef4444`).

---

## Quick Start

### 1. Launch the Server
```bash
./run.sh
```
Or manually:
```bash
.venv/bin/python3 -m app.db.init_db
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9035 --reload
```

Open `http://localhost:9035` in your browser or smartphone.

### 2. Default Seed Profiles
- **Mom:** PIN `1234` (Rose avatar)
- **Dad:** PIN `5678` (Blue avatar)

### 3. Run Automated Tests
```bash
.venv/bin/pytest -v
```
Verifies database isolation, PIN authentication, logistics CRUD, financial commitments, and timeline aggregation.
