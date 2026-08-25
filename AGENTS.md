# AGENTS.md — Task Tracker

Repo-level instructions for any AI agent (Claude Code, Codex App, Cursor,
Copilot, etc.) working in this repository. This file is project memory, not
decoration — it should be corrected by hand whenever it drifts from the
actual code.

## Project summary

A small in-memory Kanban task tracker built across an AUB AI-Assisted
Coding course (Modules 1-5). Backend: FastAPI + Pydantic v2, storage is a
single module-level Python dict (`app/storage.py`), no database. Frontend:
a single static `frontend/index.html` file (vanilla HTML/CSS/JS, no build
step, no framework). Tests: pytest against FastAPI's `TestClient`, 46 tests
in `tests/test_tasks.py`, all against the real in-memory storage (no
mocking).

## Actual tech stack

From `requirements.txt`:

- Python 3.11 (`python3 --version` in this environment reports 3.11.15)
- FastAPI (`fastapi>=0.110`)
- Pydantic v2 (`pydantic>=2.6`)
- Uvicorn (`uvicorn[standard]>=0.29`)
- pytest (`pytest>=8.0`)
- httpx (`httpx>=0.27`, used by FastAPI's `TestClient`)

No ORM, no database driver, no auth library, no frontend framework/build
tool are present anywhere in `requirements.txt` or `frontend/index.html`.

## Install / run / test commands

These are the actual commands from `README.md`, verified against this repo:

```bash
# install
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# run the API
uvicorn app.main:app --reload --port 8000
# health check
curl http://localhost:8000/health

# run the frontend (separate terminal)
cd frontend && python -m http.server 5500
# open http://localhost:5500/index.html

# run the test suite
pytest tests/ -v

# run the standalone Module 2 model-verification script
python -m tests.verify_a
```

## Important project folders

- `app/` — FastAPI backend: `main.py` (routes + CORS), `models.py`
  (Pydantic v2 request/response models), `storage.py` (in-memory dict +
  CRUD + filtering), `business_rules.py` (status-transition rules).
- `frontend/` — one file, `index.html`. IIFE module pattern, no build step.
- `tests/` — `test_tasks.py` (46 pytest tests), `conftest.py` (fixtures:
  `client`, `created_task`, autouse `_reset_storage`), `verify_a.py`
  (standalone Module 2 script, not pytest).
- `docs/` — course evidence and documentation. `docs/baseline-build-log.md`
  (Modules 1-3), `docs/midcourse/` (mid-course project: due dates + tags
  features), `docs/decisions/` (technical decision notes), plus the Module
  5 / final-project artifacts this file's guardrails apply to.

## Business rules visible in the code

- **Status transitions** (`app/business_rules.py`): only
  `ToDo->InProgress`, `InProgress->Done`, `Done->InProgress` are legal.
  Same-status "transitions" are rejected. Anything else (including
  `ToDo->Done` directly) returns HTTP 422 with a message listing the
  allowed transitions.
- **Title validation** (`app/models.py`, `_validate_title`): required,
  non-blank after `.strip()`, max 200 characters (`MAX_TITLE_LENGTH`).
  On `TaskUpdate`, an explicit `null` title is also rejected (422) — a
  fix added after a facilitator-reported gap, see
  `docs/midcourse/verification.md`.
- **Due dates** (`app/models.py`): optional `due_date` (Pydantic `date`,
  no time-of-day). `is_overdue` is a `@computed_field`, derived fresh on
  every read from `due_date` and `status` (never stored) — a task is
  overdue only if `due_date < today` AND `status != Done`.
- **Tags** (`app/models.py`, `_validate_tags`): optional `tags: List[str]`,
  default `[]`. Each tag is trimmed; blank/whitespace-only tags are
  rejected; max 5 tags per task; max 20 characters per tag. No separate
  `Tag` model or table — tags live directly on the task.
- **Partial updates** (`app/storage.py`, `update_task`): PATCH uses
  `payload.model_dump(exclude_unset=True)` — only fields actually present
  in the request body are applied. This is why `TaskUpdate`'s per-field
  validators (title, tags) only run when the client supplies that field.

## Existing validation conventions

- Validation lives in Pydantic v2 `field_validator`s on the request models
  (`TaskCreate` / `TaskUpdate`), not in ad-hoc route-level `if` checks.
  `app/main.py`'s routes stay thin.
- Both models use `model_config = ConfigDict(extra="forbid")` — an unknown
  field in the request body is a 422, not silently ignored.
- Shared validation logic is factored into module-level helper functions
  (`_validate_title`, `_validate_tags`, `_is_overdue`) called from both
  `TaskCreate` and `TaskUpdate` validators, rather than duplicated.
- Server-managed fields (`id`, `created_at`, `updated_at`, `is_overdue`)
  are never accepted from client input — they only exist on `TaskResponse`.

## CORS

`app/main.py` allows exactly `http://localhost:5500` and
`http://127.0.0.1:5500` (the two origins the frontend is actually served
from in local dev), not a wildcard. If you serve the frontend from a
different port, that origin must be added explicitly.

## Module 5 / final-project boundaries

- **Default posture is read-only analysis.** Prefer reading and reporting
  over editing. Required Module 5 / final-project edits live under `docs/`
  (plus the specific final-project exceptions below) — treat any other
  edit as out of scope unless explicitly requested.
- **Do not modify `app/` or `frontend/`** except for a small, clearly
  justified bug fix, security fix, or documentation-supported correction —
  and if you do, explain the change in `docs/final-ai-review.md`.
- **No new product features.** In particular: do not implement a comments
  feature, authentication, a production database, notifications, or
  unrelated UI changes. Comments are planned in
  `docs/decisions/comments-feature-plan.md` and must stay a plan, not code.
- **Docs-first workflow.** Deliverables for this phase are markdown files
  under `docs/` (security review, governance worksheet, AI usage rules,
  architecture documents, playbook, release evidence, final AI review),
  plus `.github/workflows/ci.yml`, `Dockerfile`, and `.dockerignore` for
  release readiness. These files did not exist before Module 4/5 work and
  are additive, not replacements for existing app code.
- **Cite actual repository files when making claims.** Do not invent file
  paths, test names, endpoints, or commands. If something is not visible
  in the files actually read, say so explicitly instead of guessing.
- **Do not invent missing structure.** This repo has no database, no auth,
  no ORM, and no frontend build step. Do not assume any of these exist.
- **Conservative permissions.** Prefer "allow once" over standing
  approval for anything that edits files or runs shell commands. Ask
  before a broad or irreversible action.
- **No secrets or destructive commands.** Never paste `.env` values,
  credentials, tokens, or real personal/customer data into this repo or
  into an AI tool. Never run destructive git operations (`push --force`,
  history rewrites, branch deletion) without explicit human confirmation.
  This project has no real user data — only course/toy data — so there
  should never be a legitimate reason to handle real secrets here.
