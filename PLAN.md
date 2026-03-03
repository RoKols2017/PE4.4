# Implementation Plan: Landing + Website Assistant (Flask)

Branch: feature/telegram-bot-lead-capture
Created: 2026-03-02
Mode: fast plan (saved in root due `.ai-factory/` permission limits)

## Settings
- Testing: yes
- Logging: verbose
- Docs: yes

## Planning Notes
- AIF priorities: bounded scope, clear module boundaries, observability-first, and incremental delivery.
- Role focus: fullstack + AI engineering for web intake assistant (lead collection, not sales automation).
- Backend is fixed: Python 3.12 + Flask, minimal dependencies, deploy-ready.
- Interaction path is fixed: landing widget (frontend) -> Flask API (backend) -> Google Sheets.
- Assistant flow is fixed: `name -> contact (phone/email) -> request -> confirm`.
- Website and Telegram bot use one shared spreadsheet; source split is done via `source` value.
- No extra operational scripts (`run.sh`, `run.bat`, etc.); only required runtime files.

## Commit Plan
- **Commit 1** (after tasks 1-3): `feat(web): scaffold flask service and shared contract`
- **Commit 2** (after tasks 4-6): `feat(web): implement dialog api, widget UX, and sheets writes`
- **Commit 3** (after tasks 7-8): `test(web): add coverage and finalize deployment docs`

## Tasks

### Phase 1: Foundations and Shared Contract
- [x] **Task 1: Scaffold Flask app with minimal deploy-ready structure**  
  Deliverable: create readable Flask project layout with strict module boundaries (`app`, `config`, `routes`, `ai_logic`, `sheets`, `session`, `domain`) and minimal dependency set.  
  Files: `web_assistant/app.py`, `web_assistant/config.py`, `web_assistant/routes.py`, `web_assistant/requirements.txt`, `web_assistant/__init__.py`.  
  Logging requirements: startup/service metadata at `INFO`, config/env validation trace at `DEBUG`, invalid bootstrap state at `ERROR`.

- [x] **Task 2: Define shared sheet contract for website email support (without breaking bot)**  
  Deliverable: formalize how website `email` is persisted in the shared Telegram+website sheet; include compatible schema strategy and row-mapping rules for `source=website_assistant`.  
  Files: `web_assistant/domain.py`, `web_assistant/sheets_schema.py` (or constants in `sheets.py`), plan note updates in `README.md`/`docs/configuration.md` for shared-sheet contract.  
  Logging requirements: mapping/contract checks at `DEBUG`, accepted normalized payload summary at `INFO`, incompatible schema or mapping conflicts at `WARN/ERROR`.

- [x] **Task 3: Build one-page landing and widget shell with fixed UX constraints**  
  Deliverable: landing page with always-available bottom-right chat widget, dark neutral style, autoscroll, and visible "assistant typing" state placeholder.  
  Files: `web_assistant/templates/index.html`, `web_assistant/static/css/styles.css`, `web_assistant/static/js/widget.js`.  
  Logging requirements: client interaction events (`open`, `send`, `scroll`, `typing_state`) at `DEBUG` (safe payloads only), rendering failures at `WARN`.

### Phase 2: Assistant Runtime and Persistence
- [x] **Task 4: Implement AI policy layer for polite bounded assistance** (depends on 1, 2)  
  Deliverable: LLM wrapper with policy prompt that keeps friendly-business tone, asks clarifying questions, avoids fabrication, and returns user to scenario when off-script.  
  Files: `web_assistant/ai_logic.py`.  
  Logging requirements: prompt stage metadata at `DEBUG` (no raw secrets/PII dumps), successful model call at `INFO`, model timeout/failure at `ERROR`, fallback activation at `WARN`.

- [x] **Task 5: Implement Flask dialog/session API for lead collection** (depends on 1, 3, 4)  
  Deliverable: API endpoints for step transitions and confirmation flow with session correlation, input validation responses, and typing-indicator state support for UI.  
  Files: `web_assistant/routes.py`, `web_assistant/session.py`, optional request/response schema helpers.  
  Logging requirements: request correlation id and step transitions at `DEBUG/INFO`, off-script/user recovery events at `WARN`, unhandled API exceptions at `ERROR`.

- [x] **Task 6: Implement shared Google Sheets adapter + infra wiring for website assistant** (depends on 2, 5)  
  Deliverable: append website leads to the same sheet used by Telegram bot with schema/bootstrap checks, retry policy, and `lead_id`; wire `docker-compose` and nginx route to Flask web assistant service.  
  Files: `web_assistant/sheets.py`, `docker-compose.yml`, `infra/nginx/default.conf`, `web_assistant/config.py`.  
  Logging requirements: schema/bootstrap events at `INFO/WARN`, outbound Sheets API calls at `DEBUG`, successful write with `lead_id` at `INFO`, retries at `WARN`, hard failures at `ERROR`.

### Phase 3: Quality and Operability
- [x] **Task 7: Add tests for contract, flow, and persistence boundaries** (depends on 2, 5, 6)  
  Deliverable: automated tests for domain validation (`phone/email`), dialog transitions, AI fallback behavior, shared-sheet mapping correctness, and mocked Sheets persistence failures.  
  Files: `web_assistant/tests/test_domain.py`, `web_assistant/tests/test_dialog.py`, `web_assistant/tests/test_sheets.py`, optional API tests (`test_routes.py`).  
  Logging requirements: test mode supports verbose logs, failure-path assertions include structured error context.

- [x] **Task 8: Update docs and project map for landing + website assistant rollout** (depends on 1-7)  
  Deliverable: update runtime docs for Flask service, shared-sheet contract, env matrix, docker/nginx startup, and troubleshooting signals; sync project map with new directories/entrypoints.  
  Files: `README.md`, `AGENTS.md`, `docs/getting-started.md`, `docs/configuration.md`, `docs/deployment.md`.  
  Logging requirements: document operational markers (`assistant_step`, `typing_state`, `lead_saved`, `sheets_retry`, `assistant_fallback`, `api_error`).
