[← Architecture](architecture.md) · [Back to README](../README.md) · [API →](api.md)

# Workflow

## Overview

Both channels use the same lead-capture pipeline:

1. collect `name`
2. collect `contact`
3. collect `request`
4. ask for `confirm`
5. save to PostgreSQL and reset the session

The main difference is the transport layer:

- Website uses HTTP endpoints and a browser widget.
- Telegram uses bot commands and text messages.

## Shared Lead-Capture Rules

- Validation runs on every step before the workflow moves forward.
- If the value looks like the wrong field type, the user stays on the same step.
- Invalid attempts are tracked in session state via `offscript_count` and `qa_flags`.
- AI is limited to a narrow JSON contract: intent hint, candidate fields, clarification flag, and a short user-facing message.
- AI is used only for phrasing, intent hints, and candidate extraction; it does not decide state transitions or final saved structure.
- If model output is empty, malformed, or contradictory, the backend must fall back to deterministic copy and validator-led flow.
- Final confirmation stores the lead in PostgreSQL and clears the session.

## Website Workflow

### Entry Point

- User opens `/` and interacts with the embedded widget.
- The frontend starts a session with `POST /api/chat/start`.
- Backend creates or reuses `session_id` and returns the first prompt for `name`.

### Step-by-Step Flow

1. `name`
   - Input is validated with `validate_name(...)`.
   - Valid names are normalized with `normalize_name(...)`.
   - Invalid names keep the session on the same step.
2. `contact`
   - Input is parsed into `phone` or `email`.
   - Validation rejects free-form request text or malformed contact data.
3. `request`
   - Input is validated as a short free-form request.
   - Contact-like values are rejected and retried.
4. `confirm`
   - User sees a summary with `name`, `contact`, and `request`.
   - `да` saves the lead.
   - `нет` resets the flow back to `name`.
   - `исправь имя` / `исправь контакт` / `исправь задачу` returns only to the selected field.

### Persistence

- Successful confirmation calls `save_website_lead(...)`.
- The record is stored with `lead_id`, `session_id`, source, and quality metadata.
- The in-memory website session is reset after save.

## Telegram Workflow

### Entry Point

- User starts with `/start` or restarts with `/new`.
- Bot resets the session bound to `chat_id`.
- Bot sends an introduction and asks for `name`.

### Step-by-Step Flow

1. `name`
   - Input is validated and normalized.
   - Invalid values keep the user on the same step.
2. `contact`
   - Input is parsed into `phone` or `telegram_username`.
   - Profile username is not silently committed as a fallback contact; the bot asks for an explicit contact value.
3. `request`
   - Input must describe the user's task.
   - Contact-like input is rejected.
4. `confirm`
   - Bot shows summary with `name`, `phone`, `telegram`, and `request`.
   - `да` saves the lead.
   - `нет` resets the flow and starts over.
   - `исправь имя` / `исправь контакт` / `исправь задачу` returns only to the selected field.

## Response Policy Layer

- `gpt-4o-mini` returns JSON only.
- The response schema is restricted to `detected_intent`, `candidate_fields`, `needs_clarification`, and `user_facing_message`.
- Candidate fields from mixed input are accepted only after deterministic field-level validation.
- If the model suggests something invalid, backend validators win.
- Confirm, edit requests, retries, and persistence decisions are resolved in deterministic code, not in the model.

### Persistence

- Successful confirmation builds a lead record and calls `save_lead(...)`.
- The record is stored with `lead_id`, source user metadata, and quality metadata.
- The Telegram session is reset after save.

## Current Weak Spots

- Session state still lives only in memory, so unfinished dialogs are lost after a restart.
- The contract is intentionally narrow, so model behavior must stay simple and strongly tested.
- The workflow has no built-in deduplication or anti-spam protection before save.

## Recommended Improvements

### Reliability

- Move session state from in-memory stores to PostgreSQL or Redis.
- Add session TTL and cleanup for abandoned dialogs.
- Add duplicate detection by contact and recent lead history.

### UX

- Show explicit progress like `Step 1 of 4`.
- Allow editing `name`, `contact`, or `request` directly from the confirmation step.
- Return clearer retry messages such as “this looks like a request, but I need a contact here.”

### Conversion

- Support multiple contact values in one message where possible.
- Reuse known website context to prefill contact or skip ahead.
- Reduce unnecessary restarts when only one field is wrong.

### Analytics

- Track where users drop off most often.
- Separate recovery metrics for website and Telegram flows.
- Persist structured reasons for retries and restarts for funnel analysis.

## See Also

- [Architecture](architecture.md) - service boundaries and data model
- [API](api.md) - HTTP endpoints used by the website flow
- [Configuration](configuration.md) - runtime variables and logging context
