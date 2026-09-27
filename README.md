# Domus - Your Home, Organised 🏡

[![Version](https://img.shields.io/badge/version-v0.2.0-blue.svg)](https://github.com/wereboss/domus/releases/tag/v0.2.0)
[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PWA](https://img.shields.io/badge/PWA-offline--first-purple.svg)](app/static/manifest.json)

Domus is an offline-first Progressive Web App (PWA) designed for parents to manage household logistics and finances with low cognitive friction and high situational durability.

---

## Architecture Foundation

- **Database Layer (Strict Dual SQLite WAL Isolation):**
  - `data/logistics.db`: Household members, tasks, chores, notes with image/document attachments, and `unprocessed_inbox`.
  - `data/finance.db`: Daily ledger expenses, recurring fixed bills.
  - Physically decoupled database engines with SQLite WAL mode enabled.
- **Backend Core:** FastAPI asynchronous API orchestrator.
- **Frontend App Shell:** Single-Page PWA built with HTML5, Pico.css, Alpine.js, and Dexie.js (IndexedDB).
- **Authentication:** Lightweight 4-digit PIN authentication per household member with persistent device sessions and instant profile switching.
- **Unified Timeline:** In-memory chronological aggregator interleaving overdue tasks, due bills, timed events, and daily chores into a single glanceable feed.
- **Mobile Capture Engine (Phase 2):**
  - **OS Web Share Target:** Intercepts shared links, text, and images directly from native share sheets into `unprocessed_inbox`.
  - **In-App Quick Capture:** 1-tap clipboard paste and native camera / PDF picker.
  - **Family Inbox Triage Deck:** 48×48px touch targets to convert unorganized inputs directly into Tasks, Expenses, or Notes.
  - **Note Media Attachments:** Embedded photo & document previews in Household Notes and Triage sheets.
  - **Smart PWA Installation Guidance:** Auto-detection for Android 1-tap install and iOS Safari Share sheet.

---

## Deployment & Run Options

### Option 1: Native Python Run
```bash
# Setup virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run server on port 9035
./run.sh
```
Or use the CLI command:
```bash
python3 -m app
```
Visit `http://localhost:9035` or your LAN address (`http://192.168.x.x:9035`).

### Option 2: Docker / Docker Compose
Run Domus in a detached, persistent container:
```bash
docker compose up -d
```
All database records and file attachments are stored in the mounted `./data` directory.

### Option 3: Remote Family HTTPS Access via Tailscale
To access Domus securely from anywhere with a valid Let's Encrypt SSL certificate and install it as a standalone PWA on Android & iOS:
```bash
# Serve within your private tailnet
sudo tailscale serve --bg 9035

# Or expose securely to the internet (no Tailscale app required on family phones)
sudo tailscale funnel --bg 9035
```
Access at your machine's MagicDNS domain: `https://<machine>.<tailnet>.ts.net`.

---

## Default Seed Profiles

- **Mom:** PIN `1234` (Rose avatar)
- **Dad:** PIN `5678` (Blue avatar)

---

## Automated Verification

Run the test suite across DB isolation, PIN auth, timeline aggregation, inbox triage, and media upload routes:
```bash
.venv/bin/pytest -v
```
All 22 unit & integration tests pass with 100% assertions.
