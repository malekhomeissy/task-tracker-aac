# Architecture — Strategy B: Structured Context (AGENTS.md + File Summaries)

**Context given to produce this document:** the full text of this
repo's `AGENTS.md`, plus prose summaries of each source file — *not* the
raw file contents. The summaries used were:

> - `app/main.py`: FastAPI app with CORS middleware and five task CRUD
>   routes (`POST/GET/GET-by-id/PATCH/DELETE /tasks`) plus `/health`.
>   PATCH also runs a status-transition check before saving.
> - `app/models.py`: Pydantic v2 models — `TaskCreate`, `TaskUpdate`,
>   `TaskResponse` — with fields title, description, status, priority,
>   assignee, due_date, tags. Title and tags have validation rules
>   (length caps, blank rejection). `is_overdue` is computed, not stored.
> - `app/storage.py`: in-memory storage, no database.
> - `app/business_rules.py`: enforces which status transitions are legal.
> - `frontend/index.html`: vanilla JS Kanban board, drag-and-drop between
>   status columns, a modal for create/edit.
> - `tests/test_tasks.py`: pytest suite covering CRUD, validation, status
>   transitions, due dates, tags.

## Architecture description

The Task Tracker is a FastAPI backend (`app/main.py`) with five REST
routes for task CRUD plus a health check, backed entirely by an in-memory
store (`app/storage.py`) — there is no database, which matches the
"course learning project" framing in `AGENTS.md`. Request/response
validation is handled by Pydantic v2 models in `app/models.py`, which
follow a consistent validation pattern across the task's text fields:
values are trimmed of whitespace, rejected if blank, and capped at a
maximum length — this applies to `title` and to `tags`, and by the same
pattern almost certainly to `description` and `assignee` as well, since a
project this disciplined about one field wouldn't leave the others
completely unbounded. Status changes go through a separate business-rules
check (`app/business_rules.py`) that enforces a fixed set of legal
transitions, keeping that logic out of the route handlers themselves. The
frontend (`frontend/index.html`) is a single-file vanilla JS Kanban board
with drag-and-drop, talking to the backend over `fetch`. The whole system
has no authentication layer, which `AGENTS.md` frames as an intentional
course-scope decision, not an oversight. Tests (`tests/test_tasks.py`)
cover the CRUD surface, validation rules, and status-transition rules
described above at a good level of depth.

## What became more complete than Strategy A

Every top-level architectural fact in Strategy A that was invented is
correctly identified here: no database (in-memory only), no auth, vanilla
JS frontend with no build step, no `User` entity. The five routes, the
computed `is_overdue` field, and the separate business-rules module are
all named specifically and correctly, none of which a one-line prompt
(Strategy A) could have produced.

## What became more specific — and where that specificity tipped into
overconfidence

The claim that `description` and `assignee` "almost certainly" have the
same length-cap/blank-rejection validation as `title` and `tags` is
**wrong**, and it's a direct product of this strategy's failure mode: a
prose summary described the *pattern* ("title and tags have validation")
without listing which fields *don't* have it, and the write-up filled the
gap by extrapolating a rule from two data points ("a project this
disciplined... wouldn't leave the others completely unbounded") instead
of stating "not confirmed." The real repo (verified directly by reading
`app/models.py` in Strategy C, and independently in `docs/security-review.md`,
finding AI-1) has `description: Optional[str] = ""` and
`assignee: Optional[str] = None` with **no validator at all** — completely
unbounded length, no blank rejection. This is exactly the kind of
plausible-sounding but false specific claim that a summary-based context
strategy is prone to producing: it had enough real information to sound
authoritative, but not enough to actually verify the one detail it
extrapolated.
