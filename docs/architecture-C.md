# Architecture — Strategy C: Targeted Context (Three Anchor Files Only)

**Context given to produce this document:** the raw, complete contents of
exactly three files — `app/main.py`, `app/models.py`, `app/storage.py` —
and nothing else. Not `AGENTS.md`, not `app/business_rules.py`, not the
frontend, not the tests, not the README, not any config or CI file. Any
claim below that isn't directly supported by one of those three files is
explicitly marked "not visible from the files I read" rather than
inferred or guessed.

## What the three files directly show

**`app/main.py`:** a FastAPI app (`app = FastAPI(title="Task Tracker
API")`) with CORS middleware allowing exactly two origins
(`http://localhost:5500`, `http://127.0.0.1:5500`) with `allow_methods`
and `allow_headers` both set to `["*"]`. Six routes: `GET /health`,
`POST /tasks`, `GET /tasks` (with optional `status`/`priority`/`overdue`/
`tag` query filters), `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}`,
`DELETE /tasks/{task_id}`. Every route is a plain `def`, not `async def`.
`GET`/`PATCH /tasks/{task_id}` raise a 404 with an explicit `detail`
message when the task doesn't exist. `PATCH` calls a function
`validate_status_transition(existing.status, payload.status)`, imported
from `app.business_rules`, before saving — so a module `app/
business_rules.py` exists and is used to gate status changes, but its
internal logic (which transitions are legal) is **not visible from the
files I read**.

**`app/models.py`:** three Pydantic v2 models — `TaskCreate`,
`TaskUpdate`, `TaskResponse` — all with `model_config =
ConfigDict(extra="forbid")`. Fields: `title` (str, required on create),
`description` (`Optional[str] = ""`), `status` (`TaskStatus` enum:
`TODO`/`IN_PROGRESS`/`DONE`), `priority` (`TaskPriority` enum:
`LOW`/`MEDIUM`/`HIGH`), `assignee` (`Optional[str] = None`), `due_date`
(`Optional[date] = None`), `tags` (`List[str]`, default empty). `title`
is validated by `_validate_title()`: trimmed, rejected if blank, capped
at `MAX_TITLE_LENGTH = 200`. `tags` is validated by `_validate_tags()`:
capped at `MAX_TAGS = 5` items, each trimmed, rejected if blank, capped
at `MAX_TAG_LENGTH = 20` characters. **`description` and `assignee` have
no field validator at all in this file** — no length cap, no blank
rejection. `TaskUpdate.title`'s validator explicitly raises on `None`
(rejects `{"title": null}`) while treating an omitted `title` as valid,
per the docstring comment in the file. `TaskResponse.is_overdue` is a
`@computed_field` — not a stored field — computed via a module-level
`_is_overdue(due_date, status)` function using `date.today()` and
excluding `DONE`-status tasks.

**`app/storage.py`:** a single module-level dict, `_tasks: dict[str,
TaskResponse] = {}` — this is the entire persistence layer. No database,
no ORM, no file I/O. `add_task` generates `id` via `uuid4().hex` and
`created_at`/`updated_at` via `datetime.now(timezone.utc)`. `update_task`
uses `payload.model_dump(exclude_unset=True)` plus `existing.model_copy
(update=changes)` — meaning a PATCH only overwrites fields the client
actually included in the request body. `get_all_tasks` filters
sequentially by `status`, `priority`, `overdue` (via `t.is_overdue`), and
`tag` (via `tag in t.tags`), each an independent optional narrowing step.
A `_reset()` function exists to clear all data — its caller is **not
visible from the files I read**, but the function's own docstring
("Used by tests...") states its purpose.

## Explicitly not visible from the files I read

- Whether there is a frontend at all, and if so what it looks like or how
  it's built — `frontend/` was not one of the three files read.
- What automated tests exist, how many, or what they cover — `tests/`
  was not read.
- The actual status-transition rules enforced by
  `validate_status_transition()` — only that it exists, is imported from
  `app.business_rules`, and is called before every status-changing PATCH.
- Whether there is a CI pipeline, a Dockerfile, or any deployment
  configuration.
- Whether there is any documentation (README, `AGENTS.md`, or otherwise)
  describing intent, setup instructions, or design rationale beyond what
  the code comments in these three files state directly.
- Whether authentication exists anywhere else in the project — these
  three files show no auth-related import or dependency, but that's
  different from confirming none exists anywhere in the repo.

This document is deliberately narrow. Its value is that every claim in
"What the three files directly show" can be checked against those exact
three files with no interpretation gap — there is nothing here that
required guessing.
