# Implementation Plan: Python Telegram Bot Lead Capture

Branch: feature/telegram-bot-lead-capture
Created: 2026-03-02
Intended path: .ai-factory/plans/feature-telegram-bot-lead-capture.md (blocked by directory permissions)

## Settings
- Testing: yes
- Logging: verbose
- Docs: yes

## Planning Notes
- Source request is used as input, but plan follows AIF priorities: clear boundaries, observable behavior, validation-first flow, and incremental delivery.
- Main delivery target remains `bot/` with Python 3.12 + telebot + OpenAI + Google Sheets + dotenv.
- Architecture is adapted: thin entrypoint + separated AI, Sheets, config, and domain/dialog logic.

## Commit Plan
- **Commit 1** (after tasks 1-3): `feat(bot): scaffold python service and config validation`
- **Commit 2** (after tasks 4-6): `feat(bot): implement dialog flow and sheets persistence`
- **Commit 3** (after tasks 7-8): `test(bot): add coverage and update run documentation`

## Tasks

### Phase 1: Foundation and Safety
- [x] **Task 1: Create Python runtime skeleton and dependency baseline**  
  Deliverable: bootstrap `bot/` package layout with executable entrypoint and dependency lock baseline for Python 3.12.  
  Files: `bot/bot.py`, `bot/requirements.txt`, `bot/__init__.py` (optional), `.gitignore` updates if needed.  
  Logging requirements: startup banner at `INFO`, runtime/env checks at `DEBUG`, dependency/init failures at `ERROR`.

- [x] **Task 2: Implement configuration loading and strict env validation**  
  Deliverable: central config loader for Telegram/OpenAI/Sheets credentials, defaults for non-sensitive vars, and fail-fast validation.  
  Files: `bot/config.py`, `bot/.env.example` (safe template only).  
  Logging requirements: config validation steps at `DEBUG`, safe config snapshot at `INFO` (never secrets), missing/invalid vars at `ERROR`.

- [x] **Task 3: Define lead domain model and validation rules**  
  Deliverable: domain object and validators for `name`, `contact` (phone or telegram username), `request`, `source=telegram_bot`, including normalization and error codes.  
  Files: `bot/domain.py` (or `bot/lead.py`), integration points in `bot/bot.py`.  
  Logging requirements: validation entry/exit at `DEBUG`, accepted payload summary at `INFO`, validation rejects with reason codes at `WARN`.

### Phase 2: Integrations and Dialog Flow
- [x] **Task 4: Implement Google Sheets adapter with retries and correlation id** (depends on 2, 3)  
  Deliverable: ensure `Leads` sheet exists and matches `.ai-factory/DATA_MODEL.md` columns (`A:R`); if missing, create sheet and write header row once; then append validated leads with retry policy, timeout handling, and generated `lead_id`.  
  Files: `bot/sheets.py`, minor wiring in `bot/config.py`.  
  Logging requirements: sheet/schema check results at `INFO`, header/bootstrap actions at `WARN` (one-time infra event), API call boundaries at `DEBUG`, successful append with `lead_id` at `INFO`, retry attempts at `WARN`, final failure context at `ERROR`.

- [x] **Task 5: Implement AI response module with bounded prompt strategy** (depends on 2, 3)  
  Deliverable: OpenAI client wrapper that generates assistant replies per current step, prevents fabrication, and supports graceful fallback if model call fails.  
  Files: `bot/ai_logic.py`.  
  Logging requirements: prompt stage metadata at `DEBUG` (no sensitive raw dumps), model success at `INFO`, OpenAI failures/timeouts at `ERROR`, fallback activation at `WARN`.

- [x] **Task 6: Build Telegram step-by-step state machine and submit workflow** (depends on 3, 4, 5)  
  Deliverable: in-memory session manager for steps `name -> contact -> request -> confirm`, off-script recovery, and final submit to Sheets.  
  Files: `bot/bot.py`, optional `bot/session.py`, optional `bot/dialog.py`.  
  Logging requirements: per-message processing at `DEBUG`, step transitions at `INFO`, off-script/user recovery events at `WARN`, unhandled exceptions at `ERROR`.

### Phase 3: Quality, Verification, and Documentation
- [x] **Task 7: Add automated tests for domain, dialog transitions, and integrations boundaries** (depends on 3, 4, 6)  
  Deliverable: unit tests for validators/session flow and integration-boundary tests with mocked OpenAI and Sheets clients.  
  Files: `bot/tests/test_domain.py`, `bot/tests/test_dialog.py`, `bot/tests/test_sheets.py` (or equivalent).  
  Logging requirements: tests support debug logging toggle, failed path assertions include structured context, error-path logs validated where practical.

- [x] **Task 8: Update runtime documentation and project map for bot delivery** (depends on 1-7)  
  Deliverable: concise run/setup docs and env matrix aligned with implemented bot behavior; keep only README as user-facing doc for `bot/` scope while syncing repo-level pointers.  
  Files: `README.md`, `AGENTS.md`, optionally `docs/getting-started.md` and `docs/configuration.md` if repo-level references changed.  
  Logging requirements: document expected log milestones (`startup`, `step_progress`, `lead_saved`, `integration_error`) and sample troubleshooting cues.
