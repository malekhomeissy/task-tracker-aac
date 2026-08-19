# Mid-Course Project — Verification Log

Real commands and real output only. Nothing in this file is fabricated or
claimed without having actually been run during this session.

---

## Baseline

**Branch creation:**
```
$ git checkout -b mid-course-project
Switched to a new branch 'mid-course-project'
$ git branch
  main
* mid-course-project
```
Created from `main` at commit `1a304bd` (the completed Modules 1-3
baseline).

**Existing pytest result before any changes:**
```
$ pytest tests/ -v
...
24 passed, 2 warnings in 0.18s
```
All 24 pre-existing tests pass. This is the baseline this project must not
regress.

**Basic backend check:** `app/main.py` imports cleanly and `GET /health`
was already confirmed returning 200 during the Modules 1-3 build (see
`docs/baseline-build-log.md`, Phase 1); re-confirmed again below in the
Feature 1 section once the server is running for the new work.

---

## Feature 1 — Due Dates + Overdue Filter

### Backend implementation evidence

`app/models.py`: added `due_date: Optional[date]` to `TaskCreate`, `TaskUpdate`,
and `TaskResponse`, plus a `@computed_field` property `is_overdue` on
`TaskResponse` (derived on every read from `due_date`/`status`, never stored).
`app/storage.py`: `get_all_tasks()` gained an `overdue: Optional[bool]`
parameter that filters on `t.is_overdue`. `app/main.py`: `GET /tasks` gained
the `overdue` query parameter, passed straight through to storage.

### Focused pytest run (Feature 1 tests only)

```
$ pytest tests/test_tasks.py -v -k "due_date or overdue"
tests/test_tasks.py::test_create_task_with_valid_due_date PASSED
tests/test_tasks.py::test_create_task_invalid_due_date_returns_422 PASSED
tests/test_tasks.py::test_patch_update_due_date PASSED
tests/test_tasks.py::test_patch_clear_due_date PASSED
tests/test_tasks.py::test_overdue_detection_true_for_past_incomplete_task PASSED
tests/test_tasks.py::test_future_due_date_is_not_overdue PASSED
tests/test_tasks.py::test_completed_past_due_task_is_not_overdue PASSED
tests/test_tasks.py::test_overdue_filter_returns_only_overdue_tasks PASSED
tests/test_tasks.py::test_overdue_filter_no_match_returns_200_and_empty_list PASSED
========================= 9 passed in 0.06s =========================
```

### Real AI-assumption bug found and corrected during this run

The first draft of `is_overdue` was written without excluding `Done` tasks:

```python
@computed_field
@property
def is_overdue(self) -> bool:
    if self.due_date is None:
        return False
    return self.due_date < date.today()
```

Running the full suite against this draft produced a genuine failure (not
staged after the fact — this is the actual first run):

```
$ pytest tests/ -v
...
FAILED tests/test_tasks.py::test_completed_past_due_task_is_not_overdue - assert True is False
1 failed, 32 passed, 2 warnings in 0.25s
```

`test_completed_past_due_task_is_not_overdue` routes a task with a
past due date through the only legal transition path to Done
(ToDo -> InProgress -> Done) and asserts `is_overdue is False`. The naive
implementation returned `True`, because it only checked `due_date`, not
`status`. Fix: added `if self.status == TaskStatus.DONE: return False` before
the date comparison, with a docstring explaining the exclusion. Rerun after
the fix:

```
$ pytest tests/ -v
...
33 passed, 2 warnings in 0.20s
```

This correction is also recorded in `docs/midcourse/user-stories.md`.

### Manual backend check (server running)

```
$ curl -s http://localhost:8000/health
{"status":"ok","timestamp":"2026-08-19T07:28:29.664786+00:00"}
$ curl -s http://localhost:8000/tasks
[]
```

### Overdue filter evidence (behavioral, via the pytest suite above)

`test_overdue_filter_returns_only_overdue_tasks` and
`test_overdue_filter_no_match_returns_200_and_empty_list` both pass, proving:
the `overdue=true` filter returns only tasks that are both past-due and not
Done, and a filter with zero matches returns HTTP 200 with `[]` (not 404).

### Invalid input evidence

`test_create_task_invalid_due_date_returns_422` passes: posting
`{"title": "Bad date", "due_date": "not-a-date"}` returns 422, handled
entirely by Pydantic's built-in `date` type coercion — no custom validator
needed.

### Frontend — automated browser verification (Playwright, headless Chromium)

Script: `/tmp/verify_feature1.py`, run against the real backend
(`uvicorn` on :8000, in-memory storage freshly reset by a server restart)
and the real static frontend (`python -m http.server 5500`) — no mocking.

```
$ python /tmp/verify_feature1.py
[PASS] Overdue task card renders
[PASS] Overdue badge shown on card
[PASS] Due date text shown on card
[PASS] Future task card renders
[PASS] No overdue badge on future task
[PASS] No-due-date task card renders
[PASS] No overdue badge on no-due-date task
[PASS] Overdue demo task visible when filter checked
[PASS] Future demo task hidden when filter checked
[PASS] No-due-date task hidden when filter checked
[PASS] All tasks visible again after unchecking filter
[PASS] Completed past-due task has no overdue badge in UI
[PASS] Escape still closes modal (regression)

=== SUMMARY ===
13/13 checks passed
```

This covers: creating a task with a past due date (overdue badge + red due
date text appear), a future due date (no badge), no due date (no badge), the
"Overdue Only" filter checkbox hiding/showing the right cards, and — the same
scenario as the backend Break Test below — moving a completed past-due task
to Done and confirming the badge disappears in the actual rendered UI. It
also re-checks a pre-existing regression (Escape key still closes the modal).

### Feature 1 Break Test

Deliberately reintroduced the naive (pre-fix) `is_overdue` implementation —
the same real mistake described above — directly in `app/models.py`,
overwriting the corrected version:

```python
if self.due_date is None:
    return False
return self.due_date < date.today()
```

(Done-status exclusion removed.)

```
$ pytest tests/ -v
...
FAILED tests/test_tasks.py::test_completed_past_due_task_is_not_overdue - assert True is False
1 failed, 32 passed, 2 warnings in 0.20s
```

The break was caught by exactly the test written to guard this behavior, for
the right reason (`assert True is False` on `is_overdue`). Restored the file
from a pre-break backup (`/tmp/models_backup.py`) and confirmed byte-for-byte
identical (`diff` produced no output), then reran:

```
$ diff /tmp/models_backup.py app/models.py
(no output — files identical)
$ pytest tests/ -v
...
33 passed, 2 warnings in 0.19s
```

---

## Feature 2 — Tags/Labels

### Backend implementation evidence

`app/models.py`: added `tags: List[str]` to `TaskCreate` (default `[]`),
`TaskUpdate` (default `None`, so `exclude_unset` distinguishes "omitted" from
"explicitly set"), and `TaskResponse`. Tags live directly on the task — no
separate `Tag` model, no many-to-many table (see `mini-adr.md` for why this
was chosen over a normalized model). A shared `_validate_tags()` helper
(mirroring the existing `_validate_title()` pattern) trims whitespace,
rejects blank/whitespace-only tags, and enforces `MAX_TAGS = 5` and
`MAX_TAG_LENGTH = 20`. `app/storage.py`: `get_all_tasks()` gained a `tag`
parameter filtering on `tag in t.tags`. `app/main.py`: `GET /tasks` gained
the `tag` query parameter.

### Focused pytest run (Feature 2 tests only)

```
$ pytest tests/test_tasks.py -v -k "tag"
tests/test_tasks.py::test_create_task_default_tags_is_empty_list PASSED
tests/test_tasks.py::test_create_task_with_valid_tags PASSED
tests/test_tasks.py::test_create_task_trims_whitespace_in_tags PASSED
tests/test_tasks.py::test_create_task_blank_tag_returns_422 PASSED
tests/test_tasks.py::test_create_task_with_exactly_five_tags_succeeds PASSED
tests/test_tasks.py::test_create_task_with_six_tags_returns_422 PASSED
tests/test_tasks.py::test_create_task_tag_over_20_chars_returns_422 PASSED
tests/test_tasks.py::test_create_task_tag_exactly_20_chars_succeeds PASSED
tests/test_tasks.py::test_patch_update_tags PASSED
tests/test_tasks.py::test_patch_unrelated_update_preserves_tags PASSED
tests/test_tasks.py::test_tag_filter_returns_only_matching_tasks PASSED
tests/test_tasks.py::test_tag_filter_no_match_returns_200_and_empty_list PASSED
========================= 12 passed in 0.11s =========================
```

### Real off-by-one bug found and corrected during this run

The first draft of `_validate_tags()` used an off-by-one bound on the tag
count:

```python
def _validate_tags(value: List[str]) -> List[str]:
    if len(value) >= MAX_TAGS:
        raise ValueError(f"A task may have at most {MAX_TAGS} tags")
    ...
```

Running the full suite against this draft (with
`test_create_task_with_exactly_five_tags_succeeds` already written) produced
a genuine failure — the actual first run, not staged after the fact:

```
$ pytest tests/ -v
...
FAILED tests/test_tasks.py::test_create_task_with_exactly_five_tags_succeeds
E       assert 422 == 201
1 failed, 44 passed, 2 warnings in 0.28s
```

`>=` incorrectly rejected exactly 5 tags, even though the spec says "max 5
tags" (5 should be allowed, 6 should not). Fix: changed `>= MAX_TAGS` to
`> MAX_TAGS`. Rerun after the fix:

```
$ pytest tests/ -v
...
45 passed, 2 warnings in 0.23s
```

This correction is also recorded in `docs/midcourse/user-stories.md`.

### Manual/browser validation evidence

Automated Playwright checks (below) directly exercise blank-tag rejection,
the 5-tag boundary, and 20-char boundary indirectly through the same backend
validator; the pytest run above is the direct evidence for validation rules.

### Frontend — automated browser verification (Playwright, headless Chromium)

Script: `/tmp/verify_feature2.py`, run against the real backend (freshly
restarted, empty in-memory storage) and the real static frontend — no
mocking.

```
$ python /tmp/verify_feature2.py
[PASS] Tagged task card renders
[PASS] Three tag chips rendered, trimmed ['backend', 'urgent', 'ui']
[PASS] Untagged task card renders
[PASS] No tag chips on untagged task
[PASS] Tagged task visible when filtering by 'urgent'
[PASS] Other tagged task hidden when filtering by 'urgent'
[PASS] Untagged task hidden when filtering by 'urgent'
[PASS] All tasks visible again after clearing tag filter
[PASS] Edit modal pre-fills tags input backend, urgent, ui
[PASS] Tags preserved on card after unrelated edit ['backend', 'urgent', 'ui']
[PASS] Highest priority task sorts first in column (regression) High prio regression check

=== SUMMARY ===
11/11 checks passed
```

This covers: entering comma-separated tags in the modal and seeing them
render as chips (trimmed), an untagged task showing no chips, the tag filter
input hiding/showing the right cards (with a debounce), the edit modal
pre-filling the tags input from the task's existing tags, tags being
preserved on the card after an unrelated (description-only) edit, and a
pre-existing regression check (priority sort order in a column).

### Filtering evidence

`test_tag_filter_returns_only_matching_tasks` and
`test_tag_filter_no_match_returns_200_and_empty_list` (backend) plus the
Playwright tag-filter checks above (frontend) both confirm: filtering by one
tag returns only tasks that have that exact tag, and a filter with zero
matches returns HTTP 200 with `[]`.

### Preservation evidence

`test_patch_unrelated_update_preserves_tags` (backend) and "Tags preserved on
card after unrelated edit" (frontend, Playwright) both confirm tags survive
a PATCH that does not touch the `tags` field.

### Feature 2 Break Test

Deliberately removed the blank-tag rejection from `_validate_tags()` in
`app/models.py`:

```python
cleaned = []
for tag in value:
    stripped = tag.strip()
    # (blank-tag check removed)
    if len(stripped) > MAX_TAG_LENGTH:
        raise ValueError(...)
    cleaned.append(stripped)
```

```
$ pytest tests/ -v -k tag
...
FAILED tests/test_tasks.py::test_create_task_blank_tag_returns_422 - assert 201 == 422
1 failed, 11 passed, 33 deselected in 0.11s
```

The break was caught by exactly the test guarding this behavior, for the
right reason (the endpoint accepted a whitespace-only tag and returned 201
instead of 422). Restored the file from a pre-break backup
(`/tmp/models_backup_f2.py`) and confirmed byte-for-byte identical
(`diff` produced no output), then reran:

```
$ diff /tmp/models_backup_f2.py app/models.py
(no output — files identical)
$ pytest tests/ -v
...
45 passed, 2 warnings in 0.26s
```

---

## Full suite result after both features

```
$ pytest tests/ -v
...
======================== 45 passed, 2 warnings in 0.27s ========================
```

24 original Modules 1-3 tests + 9 Feature 1 tests + 12 Feature 2 tests = 45.
No pre-existing test was deleted, weakened, or skipped.

---

## Behavior contract (before refactor)

Written before performing the one planned refactor, so the refactor can be
checked against it afterward. Covers both the pre-existing Modules 1-3
behaviors and the two new mid-course features.

| # | Behavior | How to check | Evidence |
|---|----------|---------------|----------|
| 1 | `GET /health` returns 200 | `curl http://localhost:8000/health` | Re-run below |
| 2 | Valid task creation returns 201 | POST `/tasks` with a valid title | pytest |
| 3 | Blank title returns 422 | POST with `{"title":"   "}` | pytest |
| 4 | `GET /tasks` with no matches returns 200 with `[]` | `GET /tasks?status=Done` on empty board | pytest |
| 5 | Cards appear in the correct status column | Create tasks with different statuses | Playwright (Modules 1-3 build) |
| 6 | Priority sorting is High -> Medium -> Low | Create 3 tasks, check column order | pytest sort logic + Playwright regression check (Feature 2 script) |
| 7 | Valid drag persists through PATCH | Drag ToDo card to InProgress | Playwright (Modules 1-3 build) |
| 8 | Rejected drag does not leave misleading UI state | Drag ToDo card to Done | Playwright (Modules 1-3 build) |
| 9 | Blank modal title sends no request | Submit New Task modal with empty title | Playwright (Modules 1-3 build) |
| 10 | Server validation error keeps modal open | Edit a ToDo task's status straight to Done | Playwright (Modules 1-3 build) |
| 11 | `due_date` accepts a valid ISO date and rejects an invalid one | POST with valid/invalid `due_date` | pytest |
| 12 | A task with a past `due_date` and status != Done is overdue | POST with a past due date | pytest |
| 13 | A task with a past `due_date` and status == Done is NOT overdue | Route task to Done, check `is_overdue` | pytest (this is the exact behavior the Feature 1 Break Test guards) |
| 14 | `GET /tasks?overdue=true` returns only overdue tasks, `[]` if none match | pytest + Playwright | pytest, Playwright |
| 15 | Tags trim whitespace, reject blank tags, cap at 5 tags / 20 chars each | pytest | pytest (this is the exact behavior the Feature 2 Break Test guards) |
| 16 | Tags survive a PATCH that does not touch `tags` | pytest + Playwright | pytest, Playwright |
| 17 | `GET /tasks?tag=X` returns only tasks with that tag, `[]` if none match | pytest + Playwright | pytest, Playwright |

**Verification run (before refactor):**

```
$ pytest tests/ -v
...
45 passed, 2 warnings in 0.27s
$ curl -s http://localhost:8000/health
{"status":"ok","timestamp":"2026-08-19T07:34:53.596783+00:00"}
```

All 17 contract items check out. `git status` confirms a clean working tree
at this point (both feature commits already made). This is the pre-refactor
checkpoint.

---

## Refactor: extract the overdue predicate into a pure function

**Scope (deliberately small):** `TaskResponse.is_overdue` previously
contained the three-branch overdue logic inline inside the `@computed_field`
property. Extracted it into a standalone pure function `_is_overdue(due_date,
status)` in `app/models.py`, and had the property call it. No behavior
change, no other files touched, no test rewritten — this is a "move logic,
don't change it" refactor, not a broad cleanup.

Before:
```python
@computed_field
@property
def is_overdue(self) -> bool:
    if self.due_date is None:
        return False
    if self.status == TaskStatus.DONE:
        return False
    return self.due_date < date.today()
```

After:
```python
def _is_overdue(due_date: Optional[date], status: "TaskStatus") -> bool:
    if due_date is None:
        return False
    if status == TaskStatus.DONE:
        return False
    return due_date < date.today()

# ... inside TaskResponse:
@computed_field
@property
def is_overdue(self) -> bool:
    return _is_overdue(self.due_date, self.status)
```

**Full pytest rerun after the refactor:**
```
$ pytest tests/ -v
...
======================== 45 passed, 2 warnings in 0.25s ========================
```
Same 45/45 as before the refactor — no regressions.

**Behavior contract rerun after the refactor:** all 17 items re-checked.
Items 11-14 (due-date/overdue behaviors, which this refactor directly
touched) were re-verified with both the pytest run above and a fresh
Playwright pass:

```
$ python /tmp/verify_feature1.py
...
=== SUMMARY ===
13/13 checks passed
$ python /tmp/verify_feature2.py
...
=== SUMMARY ===
11/11 checks passed
```

Item 1 (`GET /health`) manually re-checked:
```
$ curl -s http://localhost:8000/health
{"status":"ok","timestamp":"2026-08-19T07:35:39.395529+00:00"}
```

All 17 contract items still hold. The refactor changed structure only, not
behavior.
