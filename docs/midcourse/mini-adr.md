# Mid-Course Project — Mini Architecture Decision Record

## Decision 1: Due date representation

Store `due_date` as an `Optional[date]` (Pydantic's native `date` type,
serialized as an ISO `YYYY-MM-DD` string) directly on `TaskCreate`,
`TaskUpdate`, and `TaskResponse` — no separate "deadline" object, no
timestamp with time-of-day precision.

**Why:** the feature only ever needs a calendar date ("this is due on this
day"), never a time. Using Pydantic's `date` type gets ISO-format parsing,
validation, and normal-422-on-invalid-input for free, consistent with how
`created_at`/`updated_at` already use `datetime`. No custom validator was
needed for the date field itself (only for the derived overdue rule).

**Alternative considered and rejected:** a `datetime` with time-of-day, to
support "due by 5pm" style deadlines. Rejected as unnecessary scope — the
spec asks for a due *date*, and adding time-of-day would also complicate the
overdue comparison (would `date.today()` still be the right comparison, or
would it need `datetime.now()` and timezone handling?). Keeping it a plain
date avoids that complexity entirely.

## Decision 2: Overdue is derived, not stored

`is_overdue` is a `@computed_field` property on `TaskResponse`, recomputed
from `due_date` and `status` on every read. It is never written to storage.

**Why:** "overdue" is a function of the current date, which changes every
day without anyone editing the task. If it were stored as a persisted
boolean, every task in the system would need some kind of background job or
lazy recomputation to stay correct as calendar days pass — a task due
yesterday needs to flip from not-overdue to overdue at midnight with nobody
touching it. Deriving it on read means it is always correct with zero extra
moving parts, at the cost of a cheap comparison on every serialization
(negligible for an in-memory single-process store).

**Alternative considered and rejected:** storing `is_overdue` as a boolean
field, updated whenever a task is read or written. Rejected because it
introduces a staleness bug by construction (a task nobody touches for a week
would report stale data) and adds state that has to be kept in sync with
`due_date` and `status` by hand in every code path that touches either of
those fields. The derived approach has no synchronization problem because
there is nothing to keep in sync.

## Decision 3: Tag representation

`tags` is a plain `List[str]` field directly on `TaskCreate`, `TaskUpdate`,
and `TaskResponse` — no `Tag` model, no `tags` table, no many-to-many
relationship.

**Why:** the feature's actual requirements are narrow — a handful of short
strings per task, validated for shape (trimmed, non-blank, length-capped,
count-capped) and filterable by exact match. A `List[str]` satisfies all of
that with the same amount of code as any other field on the model, and it
fits the project's existing storage pattern: one `TaskResponse` object per
task, no relational structure anywhere else in the codebase either.

**Alternative considered and explicitly rejected:** a separate `Tag`
entity (its own id, name, maybe color) joined to tasks many-to-many. This
was the instinctive first design — "tags might need colors or a management
UI eventually, so model them properly now." It was rejected specifically
because the feature spec rules those things out (no tag colors, no tag
management UI, no autocomplete, no boolean tag-combination queries), which
means a normalized model would add real implementation cost (a second
collection, join/lookup logic, orphan-tag cleanup on delete) for
capabilities nothing in this project asks for. This is recorded as a real,
documented design-time correction — the instinct toward the "proper"
relational design had to be caught and walked back before writing any code,
not after. See `docs/midcourse/user-stories.md`, Feature 2, for the same
correction from the user-story angle.

## Decision 4: Filtering stays additive, not combinatorial

`GET /tasks` gained `overdue` and `tag` as independent optional query
parameters, following the exact same pattern as the pre-existing `status`
and `priority` filters: each filter, if present, narrows the result set
further; all are simple equality/membership checks with no boolean
combinators (no `tag=a&tag=b` OR/AND logic).

**Why:** this matches the existing filter design in `storage.get_all_tasks`
exactly, and the Feature 2 spec explicitly rules out boolean tag queries.
Extending the existing pattern was strictly simpler than inventing a new
querying mechanism for two features that both just need "match one value."
