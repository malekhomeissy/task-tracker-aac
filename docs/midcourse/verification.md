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
