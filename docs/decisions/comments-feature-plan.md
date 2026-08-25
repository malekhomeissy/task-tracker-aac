# Comments-on-Tasks Feature Plan

**Status: PLAN ONLY. Nothing in this document has been implemented.** No
files under `app/`, `frontend/`, or `tests/` were changed to produce this
plan — see `AGENTS.md`'s Module 5 boundaries section, which explicitly
names this feature as plan-only for the final project.

Feature scope, as given: a `Comment` attached to a task, with fields
`id`, `task_id`, `author` (1-100 chars), `body` (1-2000 chars), and a
server-generated UTC `created_at`.

---

## Part 1 — Generic Plan (no repo context)

This is what a first-pass plan looks like written from the feature
description alone, before opening any file in this repository. Assumptions
that turned out to need correction once the real repo was inspected are
flagged inline in Part 3.

### Data Model

- A `Comment` entity: `id` (server-generated, likely UUID or auto-increment
  integer), `task_id` (foreign key / reference to the parent task),
  `author` (string, 1-100 chars), `body` (string, 1-2000 chars),
  `created_at` (server-generated UTC timestamp).
- *Assumption:* comments are stored in a relational table with a foreign
  key to a `tasks` table, since "comments on X" usually implies a
  one-to-many relational structure in a real backend.
- *Assumption:* comments are immutable once created (no edit/update), since
  the spec only lists `created_at`, not `updated_at`.

### API Routes

- `POST /tasks/{task_id}/comments` — create a comment on a task, `201` on
  success, `404` if the task doesn't exist.
- `GET /tasks/{task_id}/comments` — list all comments for a task, ordered
  by `created_at`.
- *Assumption:* no `PATCH`/`DELETE` for individual comments, since nothing
  in the spec asks for edit or delete.
- *Assumption:* comments are only ever listed in the context of their
  parent task, never fetched globally (no `GET /comments`).

### Tests

- Create comment: valid input → 201, response includes generated `id` and
  `created_at`.
- Validation: missing `author`/`body` → 422; `author` over 100 chars → 422;
  `body` over 2000 chars → 422; `body` empty string → 422.
- 404 when `task_id` doesn't exist.
- List comments: returns in creation order; empty list when a task has no
  comments; 404 for an unknown task.
- *Assumption:* tests would live in a new `tests/test_comments.py` file,
  mirroring however the existing tests are organized (not yet verified).

### Frontend

- A comments section within each task's detail/edit view, listing existing
  comments and providing a small form (author + body) to add one.
- *Assumption:* there is some kind of per-task detail view or edit modal
  already, since "add comments to a task" implies a place to view a single
  task's details beyond the board itself. Not yet verified.

### Migration Notes

- *Assumption:* since a new entity needs a new table, this would need a
  schema migration (e.g., Alembic) if the backend uses a real database.
  Not yet verified whether one exists.

### Open Questions

- Can a comment be edited or deleted after creation?
- Is there a maximum number of comments per task?
- Does deleting a task cascade-delete its comments?
- Is `author` a free-text name or does it reference a real user/account
  system?

---

## Part 2 — Repo-Grounded Plan

This plan is built from the actual repository, after reading (in this
order) `AGENTS.md`, `app/models.py`, `app/main.py`, `app/storage.py`,
`app/business_rules.py`, `tests/test_tasks.py`, `tests/conftest.py`,
`frontend/index.html`, and `README.md`. Every claim below cites the real
file it's grounded in.

### Files inspected

`AGENTS.md`, `app/models.py`, `app/main.py`, `app/storage.py`,
`app/business_rules.py`, `tests/test_tasks.py`, `tests/conftest.py`,
`frontend/index.html`, `README.md`.

### Corrected assumptions, before the plan

Two Part-1 assumptions don't hold once the repo is actually read:

- **There is no database at all.** `requirements.txt` lists no ORM and no
  DB driver, and `app/storage.py` is a single module-level Python `dict`
  (`_tasks: dict[str, TaskResponse] = {}`), with an explicit docstring
  calling out "There is no persistence across process restarts, which is
  intentional." A `Comment` model would follow this exact same pattern —
  a second in-memory dict, not a relational table — and the "migration
  notes" section of a generic plan (Alembic, schema migrations) doesn't
  apply to this repo at all.
- **There is no per-task detail view separate from the board.** Reading
  `frontend/index.html` shows exactly one modal (`openModal`/`closeModal`,
  lines ~676-724), used for both creating a new task and editing an
  existing one via a single `<form>` (`submitForm`, line 725). There is no
  separate "task detail page." A comments UI would need to be added inside
  that same edit modal, not a new page.

### Data Model

Following the existing model file's conventions exactly
(`app/models.py`): a plain Pydantic v2 model, `extra="forbid"`, with
field-level `field_validator`s reusing the existing helper-function
pattern (`_validate_title`, `_validate_tags`) rather than inline
validation logic in the class body.

```python
# app/models.py (new additions, following the existing style)

MAX_COMMENT_AUTHOR_LENGTH = 100
MAX_COMMENT_BODY_LENGTH = 2000

def _validate_comment_author(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Author is required and cannot be blank")
    if len(stripped) > MAX_COMMENT_AUTHOR_LENGTH:
        raise ValueError(f"Author must be {MAX_COMMENT_AUTHOR_LENGTH} characters or fewer")
    return stripped

def _validate_comment_body(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Body is required and cannot be blank")
    if len(stripped) > MAX_COMMENT_BODY_LENGTH:
        raise ValueError(f"Body must be {MAX_COMMENT_BODY_LENGTH} characters or fewer")
    return stripped

class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    author: str
    body: str

    @field_validator("author")
    @classmethod
    def validate_author(cls, value: str) -> str:
        return _validate_comment_author(value)

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        return _validate_comment_body(value)

class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    task_id: str
    author: str
    body: str
    created_at: datetime
```

No `CommentUpdate` model — the spec lists no edit capability, and nothing
in the existing `TaskUpdate` pattern is reused here since there's nothing
to patch. `id` and `created_at` are server-managed, following the exact
rule stated at the top of `app/models.py`: "Server-managed fields (id,
created_at, updated_at) are never accepted from client input."

### Storage

A second in-memory dict in `app/storage.py`, matching the existing
`_tasks` pattern exactly, plus a `_reset()` extension so
`tests/conftest.py`'s autouse `_reset_storage` fixture keeps working
without changes to the fixture itself:

```python
_comments: dict[str, CommentResponse] = {}

def add_comment(task_id: str, payload: CommentCreate) -> Optional[CommentResponse]:
    if task_id not in _tasks:
        return None
    comment = CommentResponse(
        id=uuid4().hex,
        task_id=task_id,
        author=payload.author,
        body=payload.body,
        created_at=datetime.now(timezone.utc),
    )
    _comments[comment.id] = comment
    return comment

def get_comments_for_task(task_id: str) -> list[CommentResponse]:
    return [c for c in _comments.values() if c.task_id == task_id]

def _reset() -> None:
    _tasks.clear()
    _comments.clear()  # extends the existing _reset(), doesn't replace it
```

### API Routes

Following `app/main.py`'s existing route style exactly — plain `def`
handlers (not `async def`, matching every existing route), the same
404-with-`detail` pattern already used in `get_task`/`patch_task`/
`delete_task`, and the same `response_model=` + `status_code=` decorator
style:

```python
@app.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, tags=["comments"])
def create_comment(task_id: str, payload: CommentCreate) -> CommentResponse:
    comment = storage.add_comment(task_id, payload)
    if comment is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return comment

@app.get("/tasks/{task_id}/comments", response_model=list[CommentResponse], tags=["comments"])
def list_comments(task_id: str) -> list[CommentResponse]:
    if storage.get_task_by_id(task_id) is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return storage.get_comments_for_task(task_id)
```

No `PATCH`/`DELETE` routes, matching the Part-1 assumption that held up:
the spec gives no edit/delete requirement, and there's no `updated_at`
field to suggest mutability.

### Tests

New `tests/test_comments.py`, mirroring `tests/test_tasks.py`'s exact
naming convention (`test_<action>_<condition>_<result>`) and reusing the
`client`/`created_task` fixtures already defined in `tests/conftest.py`
rather than inventing new ones:

- `test_create_comment_valid_returns_201(client, created_task)`
- `test_create_comment_missing_author_returns_422(client, created_task)`
- `test_create_comment_blank_body_returns_422(client, created_task)`
- `test_create_comment_author_over_100_chars_returns_422(client, created_task)`
- `test_create_comment_body_over_2000_chars_returns_422(client, created_task)`
- `test_create_comment_unknown_task_returns_404(client)`
- `test_list_comments_empty_returns_200_and_empty_list(client, created_task)`
- `test_list_comments_returns_created_comments_in_order(client, created_task)`
- `test_list_comments_unknown_task_returns_404(client)`

### Frontend

Added inside the existing single edit/create modal (`openModal`/
`closeModal`, `frontend/index.html` lines ~676-724) rather than a new
page — but only when editing an *existing* task (a comment needs a real
`task_id`, so the comments section is hidden while `openModal(null)` is
creating a brand-new task). Following the file's existing conventions
exactly: comment text rendered through the existing `escapeHtml()`
helper (line 428) — the same function every task title/description/tag
already goes through — and a `fetch()` call shaped like the existing
`handleDrop`/`submitForm` calls (`fetch(... , {method: ..., headers:
{"Content-Type": "application/json"}, body: JSON.stringify(...)})`,
lines ~643 and ~787), reusing `formatServerError()` (line 815) for
validation-error display so 422s render the same way task-field errors
already do.

### Migration Notes

None apply — there is no database and therefore no schema migration
tooling in this repo (corrected from the Part-1 assumption above).

### Open Questions

- Can a comment be edited or deleted after creation? (Spec doesn't say;
  current plan assumes no, matching the fields given.)
- Is there a maximum number of comments per task? (No cap specified;
  `_validate_tags`'s `MAX_TAGS` pattern would be the natural place to add
  one if the course wants this addressed, e.g. a `MAX_COMMENTS_PER_TASK`
  constant enforced in `add_comment`.)
- Does deleting a task need to also delete its comments? `storage.
  delete_task` currently only removes the task from `_tasks` — a real
  implementation would need to decide whether orphaned comments in
  `_comments` are acceptable for this in-memory, no-persistence project,
  or whether `delete_task` should also purge matching comments.
- Is `author` free text (as modeled above, since there's no user/auth
  system anywhere in this repo — confirmed by `requirements.txt` and
  `AGENTS.md`) or does it need to eventually tie to a real identity? Free
  text is the only option that fits the existing repo, since there is no
  auth system to attach an identity to.

---

## Part 3 — Section-by-Section Critique

Grading each Part-1 (generic) section against what Part-2 (grounded)
found: **Right** (generic plan held up), **Missing** (generic plan omitted
something the real repo requires), or **Needs Resequencing** (generic
plan's ordering/approach doesn't fit how this repo actually works).

| Section | Grade | Why |
|---|---|---|
| Data Model | Needs Resequencing | Generic plan assumed a relational table with a foreign key. The real repo has no database — it's a plain Python dict, same as `_tasks`. The *shape* of the model (id/task_id/author/body/created_at) was right; the *storage mechanism* assumed was wrong. |
| API Routes | Right | The generic plan's route shapes (`POST`/`GET` under `/tasks/{task_id}/comments`, 404 on unknown task, no edit/delete) match the grounded plan almost exactly — this is a case where the generic instinct happened to line up with how the real repo's existing routes (`app/main.py`) are already structured. |
| Tests | Missing | Generic plan named the right test *cases* but missed that this repo has an existing, very specific naming convention (`test_<action>_<condition>_<result>`) and reusable fixtures (`client`, `created_task` in `tests/conftest.py`) that a new test file must follow, not reinvent. |
| Frontend | Missing | Generic plan assumed a "per-task detail view" that does not exist in this repo. The real UI has exactly one modal shared between create and edit. This is the single biggest gap between the two plans — building against the generic assumption would have meant designing a UI surface that isn't there. |
| Migration Notes | Needs Resequencing | The entire section doesn't apply — there is no database, so "add a migration" isn't a real step here. A generic plan defaulting to "assume there's a real database" is the wrong default for a course project like this one. |
| Open Questions | Right, with one addition | All four generic questions are still open and still worth asking. The grounded pass added one more (`author` as free text vs. real identity) that only becomes obvious once you know this repo has no auth system at all. |

### Missing details (from the generic plan)

- The single-modal frontend constraint (no detail page to attach a
  comments section to independently).
- The in-memory-only storage constraint (no DB, no migrations).
- The existing test-naming and fixture-reuse conventions.
- The existing `escapeHtml()` / error-formatting frontend helpers that a
  comments UI should reuse rather than duplicate.

### Resequencing issues

- The generic plan's "Migration Notes" section should not exist as a step
  at all for this repo — planning a migration before checking whether a
  database exists is exactly backwards for a project like this one; the
  storage mechanism should be confirmed *before* any data-model section is
  written, not after.
- The generic plan's "Frontend" section assumed a UI surface without
  first checking what UI actually exists — for this repo, reading
  `frontend/index.html` needed to happen before deciding whether the
  comments UI is a new page or an addition to the existing modal.

### Three-line comparison

- **Biggest difference:** the generic plan assumed a relational database
  and a separate task-detail page; neither exists in this repo — comments
  belong in a second in-memory dict and inside the one existing modal.
- **Which plan would I actually hand a teammate, and why:** the
  repo-grounded plan (Part 2) — it cites the exact functions, files, and
  line ranges to extend, so a teammate could start implementing
  immediately instead of first re-discovering that there's no database.
- **When is generic planning (Part 1) still good enough on its own:**
  for a brand-new project with no existing codebase to contradict it, or
  for a first pass meant purely to surface open questions before anyone
  has looked at any code — which is exactly what it was useful for here,
  as a checklist to verify against once the real repo was read.
