# Mid-Course Project — Prompt Log

Prompts actually used to drive each implementation step in this session,
broken into the focused sub-tasks they were given as (rather than one giant
undifferentiated request). AI response summaries are short; full detail is
in the actual diffs/commits and in `docs/midcourse/verification.md`.

---

## Feature 1: Due Dates + Overdue Filter

### Prompt 1.1 — backend field + model

**Purpose:** add the due-date field itself before touching anything derived
from it.

**Prompt:** "Add an optional `due_date` field to `TaskCreate`, `TaskUpdate`,
and `TaskResponse` in `app/models.py`, using Pydantic's `date` type so an
invalid date string produces a normal 422 with no custom validator needed.
Wire it through `storage.add_task` and confirm `update_task`'s existing
generic `model_dump(exclude_unset=True)` + `model_copy` logic handles PATCH
updates and clearing without any changes."

**AI response summary:** added the field to all three models, added
`due_date=payload.due_date` to `storage.add_task`, and confirmed (by reading
`update_task`) that no other storage code needed to change because it
already worked generically off `exclude_unset`.

**Outcome:** accepted as-is.

### Prompt 1.2 — derived overdue property

**Purpose:** implement the "derived, not stored" overdue rule.

**Prompt:** "Add a computed `is_overdue` property to `TaskResponse` using
`@computed_field`, so it's recalculated on every read instead of stored. A
task is overdue if it has a `due_date` in the past. Do not store this as a
database field."

**AI response summary:** implemented `is_overdue` checking only `due_date <
date.today()`.

**Outcome:** accepted initially, but this prompt under-specified the Done
exclusion — the resulting code did not check task status at all. This was
caught by the test written from Prompt 1.3, not by re-reading the prompt.
See the correction below.

### Prompt 1.3 — focused tests + the real correction

**Purpose:** write tests for due-date creation, updates, clearing, overdue
detection (including the Done-task edge case), and the overdue filter.

**Prompt:** "Write pytest tests in `tests/test_tasks.py` covering: valid due
date on create, invalid due date returns 422, PATCH updates a due date,
PATCH with `due_date: null` clears it, a past-due incomplete task is
overdue, a future-due task is not overdue, a completed task that was due in
the past is NOT overdue even though its due date is in the past, and the
`overdue` query filter on `GET /tasks` including the no-match case."

**AI response summary:** wrote 9 tests. Running the full suite immediately
surfaced a real failure:
`test_completed_past_due_task_is_not_overdue` failed with
`assert True is False`, because the Prompt-1.2 implementation never checked
`status`. Fixed `is_overdue` to add `if self.status == TaskStatus.DONE:
return False` before the date comparison, then reran — all tests passed.

**Outcome:** edited after a real test failure, not accepted as originally
written. Full evidence in `docs/midcourse/verification.md`.

---

## Feature 2: Tags/Labels

### Prompt 2.1 — design check before writing code

**Purpose:** decide the data shape before implementation, specifically to
avoid over-engineering.

**Prompt:** "Before writing any code: how would you model tags on a task
for this project? List the options and their tradeoffs, given the
constraint that this must NOT use a separate Tag model, many-to-many table,
tag colors, or a tag management UI."

**AI response summary:** the first pass toward an answer still leaned
toward a normalized `Tag` entity with its own id/name (and noted "could add
colors and a management screen later") before immediately noting that this
violates the stated constraints. Settled on `tags: List[str]` directly on
the task.

**Outcome:** the normalized-model instinct was rejected during this
planning step, before any code existed — recorded in
`docs/midcourse/mini-adr.md` (Decision 3) and `docs/midcourse/user-stories.md`
as the Feature 2 design-time correction.

### Prompt 2.2 — backend field + validation

**Purpose:** implement the agreed `List[str]` design with its validation
rules.

**Prompt:** "Add an optional `tags: List[str]` field (default empty list) to
`TaskCreate`/`TaskUpdate`/`TaskResponse`. Trim whitespace on each tag,
reject blank/whitespace-only tags with 422, cap at 5 tags per task and 20
characters per tag, both inclusive of the boundary (5 tags OK, 6 rejected;
20 chars OK, 21 rejected). Add a `GET /tasks` filter by one exact tag,
returning `[]` on no match rather than an error."

**AI response summary:** added a shared `_validate_tags()` helper and wired
it into both `TaskCreate` and `TaskUpdate` field validators, plus the
storage/route filter.

**Outcome:** accepted, then corrected after a real test failure — see
Prompt 2.3.

### Prompt 2.3 — focused tests + the real correction

**Purpose:** cover creation, trimming, rejection, boundary values, PATCH
preservation, and filtering.

**Prompt:** "Write pytest tests: default empty tags, valid tags round-trip,
whitespace gets trimmed, a blank tag is rejected, exactly 5 tags succeeds,
6 tags is rejected, a 21-character tag is rejected, a 20-character tag
succeeds, PATCH can update tags, an unrelated PATCH (e.g. description-only)
leaves existing tags untouched, and the tag filter including the no-match
case."

**AI response summary:** wrote 12 tests. Running the full suite surfaced a
real failure: `test_create_task_with_exactly_five_tags_succeeds` failed with
`assert 422 == 201`, because Prompt 2.2's implementation used
`len(value) >= MAX_TAGS` instead of `> MAX_TAGS`, an off-by-one that
rejected the boundary case the spec explicitly allows. Fixed the comparison
operator and reran — all tests passed.

**Outcome:** edited after a real test failure, not accepted as originally
written. Full evidence in `docs/midcourse/verification.md`.

---

## Prompt-quality exercise (not real production work)

The instructions for this project asked for one deliberately weak prompt,
followed by a rewrite, as an exercise in what makes a prompt effective —
this pair was not used to build any actual feature.

**Weak prompt:** "Add due dates to my task tracker."

**Why it's weak:** no role/context (which files, which stack), no
constraints (what type should the date be? is time-of-day involved? what
happens on an invalid date?), no definition of "overdue" at all, and no
success criteria the AI could check its own work against. An AI given only
this could reasonably store overdue as a persisted flag, use a full
`datetime`, or skip validation entirely — all plausible but wrong for this
project.

**Stronger rewrite:** "In this FastAPI + Pydantic v2 task tracker
(`app/models.py`, `app/storage.py`, `app/main.py`), add an optional
`due_date` field (date only, no time) to task creation and updates. Invalid
date strings should fail the same way other invalid fields already do (422,
no custom error handling). Add a read-only `is_overdue` field that is true
only when a task has a due date in the past AND its status is not Done —
this must be computed on every read, never written to storage, since it
depends on today's date. Add pytest tests, including the case where a task
is completed after its due date has passed. Do not change the existing CRUD
routes' response shape beyond adding these fields."

**What changed:** the rewrite adds role/context (exact files and stack),
the task's precise scope (date, not datetime), explicit constraints (derived
not stored, matches existing 422 behavior, the Done-exclusion edge case
named up front), and a verification expectation (tests, including the edge
case that the real Prompt 1.2 mistake above actually missed). Notably, this
stronger prompt names the exact Done-task edge case that the actual weaker
Prompt 1.2 above failed to specify — written after the fact, with the
benefit of hindsight from that real mistake.
