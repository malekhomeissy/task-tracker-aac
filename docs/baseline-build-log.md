# Task Tracker Baseline — Build Log

Reconstruction of the Modules 1–3 Task Tracker baseline from the official AUB
AI-Assisted Coding course PDFs (Module 1/2/3 Lecture Notes + Prompt Libraries).
Each entry below reflects a command that was actually run in this session and
its actual output — nothing here is fabricated.

---

## Phase 1 — Module 1 baseline (`/health`)

**Changed:** Created `app/__init__.py`, `app/main.py` (FastAPI app with a
single `GET /health` route returning `{"status": "ok", "timestamp": ...}`),
`requirements.txt`, `.gitignore`.

**Command:**
```
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
curl -s -o /tmp/health_resp.json -w "HTTP_STATUS:%{http_code}\n" http://localhost:8000/health
```

**Result:**
```
HTTP_STATUS:200
{"status":"ok","timestamp":"2026-08-18T05:00:06.767829+00:00"}
```
fastapi 0.141.1, pydantic 2.13.3 installed cleanly. PASS.

**Assumption/correction:** None needed — this phase matched the course spec
exactly on the first attempt.

---

## Phase 2 — Pydantic v2 models

**Changed:** Created `app/models.py` with `TaskStatus`, `TaskPriority`
enums and `TaskCreate` / `TaskUpdate` / `TaskResponse` models, all using
`ConfigDict(extra="forbid")` and a shared `field_validator` for title
stripping/blank/length checks.

**Command:** `python3 -c "from app.models import ..."` (manual import smoke
check, see Phase 3 entry below for combined output).

**Result:** Imported cleanly, no errors.

**Assumption/correction:** None — matched the exact field/enum spec from the
Module 2 Prompt Library (A1 prompt).

---

## Phase 3 — In-memory storage

**Changed:** Created `app/storage.py` with `_tasks: dict[str, TaskResponse]`
and `add_task`, `get_all_tasks`, `get_task_by_id`, `update_task`,
`delete_task`, `_reset`, using `uuid4().hex` for ids and
`payload.model_dump(exclude_unset=True)` for partial updates.

**Command:**
```
python3 -c "
from app.models import TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskPriority
from app.storage import add_task, get_all_tasks, get_task_by_id, update_task, delete_task, _reset
_reset()
t = add_task(TaskCreate(title='  Write tests  '))
u = update_task(t.id, TaskUpdate(status=TaskStatus.IN_PROGRESS))
delete_task(t.id); delete_task(t.id)
"
```

**Result:**
```
IMPORT_OK
created: 8a3b2651b2b0461c8d96aa1ede9e593b 'Write tests' TaskStatus.TODO TaskPriority.MEDIUM None
all: 1
updated status: TaskStatus.IN_PROGRESS updated_at changed: True
delete: True
delete again: False
```
Title was stripped correctly, defaults applied, `updated_at` changed on
update, second delete correctly returned False. PASS.

**Assumption/correction:** None needed.

---

## Phase 4 — Module 2 model verification (`tests/verify_a.py`)

**Changed:** Created `tests/verify_a.py` with 8 independent PASS/FAIL checks
against `app/models.py` (no pytest dependency, matches the course's
`python -m tests.verify_a` script pattern).

**Command:** `python3 -m tests.verify_a`

**Result:**
```
PASS: 1. whitespace-only title rejected
PASS: 2. empty title rejected
PASS: 3. title over 200 characters rejected
PASS: 4. defaults are status=ToDo, priority=Medium, description=''
PASS: 5. extra field rejected in TaskCreate
PASS: 6. id rejected in TaskCreate
PASS: 7. created_at rejected in TaskUpdate
PASS: 8. invalid status rejected

ALL CHECKS PASSED
EXIT_CODE:0
```

**Assumption/correction:** None — all 8 checks passed on the first run.

---

## Phase 5 — CRUD API

**Changed:** Extended `app/main.py` with `POST /tasks`, `GET /tasks`
(status/priority filters), `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}`
(no transition logic yet), `DELETE /tasks/{task_id}` — all on the existing
`FastAPI()` instance, wired to `app/storage.py`.

**Command:** ran the server and curled all 10 minimum-verification cases
(valid POST, invalid POST, list, filter no-match, filter match, GET
existing, GET missing, PATCH, DELETE, DELETE missing).

**Result (real curl output):**
```
1. valid POST            -> 201
2. invalid POST (blank)  -> 422 {"detail":[{...,"msg":"Value error, Title is required and cannot be blank",...}]}
3. list all               -> 200 [1 task]
4. filter status=Done      -> 200 []
5. filter priority=High    -> 200 [1 task]
6. GET existing            -> 200
7. GET missing              -> 404 {"detail":"Task with id does-not-exist not found"}
8. PATCH title-only         -> 200 (title updated, updated_at changed)
9. DELETE existing          -> 204, body 0 bytes
10. DELETE missing (same id)-> 404
```
All status codes matched the spec exactly. PASS.

**Assumption/correction:** Initially named the `GET /tasks` status query
parameter `status_filter` to avoid shadowing FastAPI's `status` module
import used for status codes. Caught this during self-review — the course
spec requires the query parameter to literally be named `status` (so
`GET /tasks?status=Done` works), and Python parameter shadowing inside a
single function body doesn't affect the module-level `status` import used
in other functions' decorators. Renamed the parameter back to `status`
before running any verification.

---

## Phase 6 — Business rules (status transitions)

**Changed:** Created `app/business_rules.py` with `VALID_TRANSITIONS`
(frozenset of the 3 allowed pairs) and `validate_status_transition`, which
raises HTTP 422 for anything not in that set (same-status included). Updated
the PATCH route in `app/main.py` to fetch the existing task first (404 if
missing), then call the validator only when `payload.status` is provided.

**Command:** ran the server and curled the exact 6-scenario transition
matrix from the course, plus one extra check for missing-task-with-status.

**Result (real curl output):**
```
T1 ToDo->InProgress        -> 200
T2 InProgress->Done        -> 200
T3 Done->ToDo               -> 422 "Invalid status transition from Done to ToDo. ..."
T4 Done->InProgress         -> 200
T5 InProgress->InProgress   -> 422 "Invalid status transition from InProgress to InProgress. ..."
T6 title-only update        -> 200
T7 missing task + status    -> 404 (confirms 404 wins over 422 when task doesn't exist)
```
Pattern `200, 200, 422, 200, 422, 200` matched exactly on the first attempt.

**Assumption/correction:** None needed — matched spec exactly.

---

## Phase 7 — Pytest suite

**Changed:** Created `tests/conftest.py` (autouse `_reset_storage` fixture,
`client` fixture, `created_task` fixture) and `tests/test_tasks.py` with 24
named tests covering create, list/filter, get, patch (including the 6
transition scenarios individually), and delete.

**Command:** `python3 -m pytest tests/ -v`

**Result:** `24 passed, 2 warnings in 0.17s` — all green on the first run.
(The 2 warnings are a Starlette `DeprecationWarning` about
`HTTP_422_UNPROCESSABLE_ENTITY` being renamed to
`HTTP_422_UNPROCESSABLE_CONTENT` in newer versions; functionally identical,
noted for the final cleanup pass.)

**Assumption/correction:** The course's own D1 prompt names 17 specific
tests, which don't include a standalone "invalid status on create" case or
an explicit "same status -> same status" case as separate tests from the
general invalid-transition test. Added
`test_create_task_invalid_status_returns_422`,
`test_create_task_title_over_200_chars_returns_422`,
`test_create_task_unknown_field_returns_422`,
`test_list_tasks_returns_created_tasks`,
`test_list_tasks_combined_status_and_priority_filter`,
`test_patch_invalid_title_returns_422`, `test_patch_same_status_returns_422`,
and `test_patch_unrelated_update_does_not_trigger_transition_validation` to
fully cover every item explicitly requested, bringing the total to 24 (the
course spec explicitly allows more than the minimum).

---

## Phase 8 — Break Test

**Changed (temporarily):** In `app/main.py`, replaced
`validate_status_transition(existing.status, payload.status)` with
`pass  # BREAK TEST: transition validation intentionally disabled` inside
the PATCH route.

**Command:**
```
pytest tests/test_tasks.py::test_patch_invalid_transition_todo_to_done_returns_422 -v   # while broken
pytest tests/ -v                                                                          # while broken
# then restore app/main.py from backup
pytest tests/test_tasks.py::test_patch_invalid_transition_todo_to_done_returns_422 -v   # after restore
pytest tests/ -v                                                                          # after restore
```

**Result:**
- While broken: `test_patch_invalid_transition_todo_to_done_returns_422` FAILED
  with `assert 200 == 422` (ToDo->Done was silently allowed). The full suite
  showed `2 failed, 22 passed` — the same failure plus
  `test_patch_same_status_returns_422` (also `200 == 422`), since both rely
  on the same validation call.
- After restoring the exact original `app/main.py` (confirmed via `diff`
  showing no differences from the pre-break backup): the targeted test
  PASSED, and the full suite returned to `24 passed, 2 warnings`.

**Assumption/correction:** None — the test failed for the expected reason
(the validation call was the thing removed, and the assertion caught the
exact behavior it was supposed to protect) and passed again cleanly after
restoration. No leftover broken code remains in `app/main.py`.

---

## Phases 9–14 — Module 3 frontend (`frontend/index.html`)

**Changed:** Built a single self-contained `frontend/index.html` (vanilla
HTML/CSS/JS, no framework, no build step) covering, in the course's build
order: static 3-column layout (ToDo/InProgress/Done, labeled To Do/In
Progress/Done) with sample-card-free empty columns; `fetchTasks()` +
`renderBoard()` wired to `GET /tasks`; explicit `loading` / `ready` /
`empty` / `error` states via a `data-state` attribute plus a Retry button;
native HTML5 drag-and-drop that PATCHes `status` on cross-column drop, skips
the network call on same-column drop, and optimistically updates with
rollback + a visible error message on 4xx/network failure; and a create/edit
modal (New Task button + per-card Edit button) with client-side title
trimming/blank rejection, server 422 display without closing the modal, and
Cancel/X/Escape/overlay-click dismissal that clears stale state.

**Key design decision:** For edit-mode PATCH requests, the form diffs the
current field values against the task snapshot captured when the modal
opened and only includes fields that actually changed in the PATCH body.
This was necessary, not optional — the backend's business rule rejects
same-status "transitions" (422), so if the form always sent the currently-
selected status back to the server, every description-only or
priority-only edit would incorrectly trigger a 422 from the transition
validator. Diffing avoids sending `status` at all unless the user actually
changed it, which is exactly the behavior Module 3's lecture notes describe
as "unrelated update does not trigger transition validation."

**Command/check:** Static review of the file plus a Python syntax/structure
pass at write time. Full functional verification (columns, sorting, fetch,
UI states, drag-and-drop, modal, CORS) is recorded below in the Phase
12/15 entry, run with Playwright against a real backend and a real static
file server rather than claimed without evidence.

**Assumption/correction:** None yet at write time — see the verification
entry below for what was actually exercised and what, if anything, needed
a fix after real testing.

---

## Phase 12 — CORS debugging from real evidence

**Changed (evidence step, before any code change):** Ran the backend on
port 8000 and `frontend/index.html` on a separate local static server
(`python -m http.server 5500`) — two different local origins, exactly as
the lecture notes describe — and loaded the page in real headless Chromium
via Playwright, **before** adding any CORS middleware.

**Command:** a one-off Python/Playwright script that launches both servers
and a real browser, navigates to `http://localhost:5500/index.html`, and
captures the browser console and network activity.

**Result (real browser console output):**
```
BOARD_STATE: error
ERROR_TEXT: Could not load tasks: Failed to fetch
CONSOLE: [error] Access to fetch at 'http://localhost:8000/tasks' from
  origin 'http://localhost:5500' has been blocked by CORS policy: No
  'Access-Control-Allow-Origin' header is present on the requested resource.
FAILED_REQUESTS: GET http://localhost:8000/tasks -> net::ERR_FAILED
```
This confirms CORS genuinely blocks the request without a fix, and confirms
the frontend's own error state correctly caught and displayed it — the
error was not manufactured, it's what a real browser did.

**Fix:** Added the smallest necessary `CORSMiddleware` to `app/main.py`,
allowing only `http://localhost:5500` and `http://127.0.0.1:5500` (the
origins actually used to serve the frontend locally).

**Re-verification (same script, after the fix):**
```
BOARD_STATE: empty
ERROR_STATE_VISIBLE: False
RESPONSES (tasks-related): 200 http://localhost:8000/tasks
```
`pytest tests/ -v` re-run after the CORS change: `24 passed, 2 warnings` —
unaffected. PASS.

**Assumption/correction:** None on the app itself — the CORS failure and
its fix are both real, evidence-based, and match the course's instruction
not to add CORS preemptively.

---

## Phase 15 — Frontend manual verification (automated with real evidence)

Cowork's environment has no interactive human, but it does have a
pre-installed headless Chromium and Playwright. Rather than claim these 19
flows were "verified" without evidence, or list them all as manual-only,
every flow that could be driven by a real browser against the real running
backend was actually executed: real HTTP requests, a real DOM, and real
HTML5 drag-and-drop events dispatched with a genuine `DataTransfer` object
so the app's own `dragstart`/`dragover`/`drop` listeners ran unmodified
(this is the standard way to drive native HTML5 DnD from an automated
browser — functionally identical to a human dragging a card).

**Command:** a Playwright script that boots the backend + static frontend
server, opens the board, and runs 17 checks covering the course's 19 listed
flows (flows 3–5, "create High/Medium/Low tasks," are combined into one
check since they're the same action three times).

**First run result:** 2 of 17 checks failed — but the failure was in the
**verification script itself**, not the product. `wait_for_selector("#modal-overlay[hidden]")`
used Playwright's default `state="visible"`, which is self-contradictory
for a selector that only matches the hidden element (it can never be both
"has attribute hidden" and "visible"). This caused a real timeout, which I
diagnosed by writing a smaller isolated repro (opening the modal, filling
the form, clicking save, and checking `page.is_hidden(...)` directly) — that
repro showed the actual POST succeeding (201) and the modal genuinely
closing, proving the product code was correct and the test helper was
wrong. Fixed the helper to `page.wait_for_selector("#modal-overlay", state="hidden")`
and reran.

**Final result (real, reproduced twice):**
```
PASS: 1. Three columns render with correct labels
PASS: 2. Empty columns show placeholders (fresh backend)
PASS: 3-5. Three tasks created and appear in ToDo column
PASS: 6. Priority ordering is High -> Medium -> Low
PASS: 7. Edit title persists and renders
PASS: 8. Edit priority reorders card to top of column
PASS: 9. Valid drag (ToDo->InProgress) sends PATCH and moves card
PASS: 10. Invalid drag (ToDo->Done) is rejected, card reverts, error shown
PASS: 11. Same-column drop sends no PATCH request
PASS: 12. Blank title shows client error and sends no request
PASS: 13. Server 422 (invalid transition via modal) keeps modal open with message
PASS: 14. Cancel closes modal
PASS: 15. X button closes modal and clears stale state
PASS: 16. Escape key closes modal and clears stale state
PASS: 17. Overlay click closes modal
PASS: 18. Stopping backend produces a visible error state
PASS: 19. Retry succeeds after backend restarts

TOTAL: 17  PASSED: 17  FAILED: 0
```

**Not covered by this automated pass (genuinely manual):** purely visual
polish/aesthetics (spacing, colors "looking right"), and real mouse-driven
drag physics (the drag was driven via a dispatched `DataTransfer`, which
exercises the same event handlers a real mouse drag triggers, but is not
literally a human moving a physical mouse). These are listed for Malek to
eyeball in the README rather than claimed as machine-verified.

**Assumption/correction:** The one real bug found and fixed was in the
Playwright test helper (`wait_for_selector` misuse), not in
`frontend/index.html` — corrected as described above before trusting the
"FAIL" results.

---

## Module 3 Behavior Contract

Written before the Phase 18 final-cleanup pass, so any last-minute tidy-up
can be checked against it. All ten items below were re-verified after
cleanup using the same Phase 15 automated script and a final `pytest`
run — see Phase 18.

| # | Behavior | How to check manually | Automated evidence |
|---|----------|------------------------|---------------------|
| 1 | `GET /health` returns 200 | `curl http://localhost:8000/health` | Phase 1 |
| 2 | Valid task creation returns 201 | `curl -X POST /tasks -d '{"title":"x"}'` | Phase 5, pytest |
| 3 | Blank title returns 422 | POST with `{"title":"   "}` | Phase 5, pytest |
| 4 | `GET /tasks` with no matches returns 200 with `[]` | `curl /tasks?status=Done` on empty board | Phase 5, pytest |
| 5 | Cards appear in the correct status column | Create tasks with different statuses, check board | Phase 15 (#1, #3-5) |
| 6 | Priority sorting is High -> Medium -> Low | Create 3 tasks, check column order | Phase 15 (#6, #8) |
| 7 | Valid drag persists through PATCH | Drag ToDo card to InProgress | Phase 15 (#9) |
| 8 | Rejected drag does not leave misleading UI state | Drag ToDo card to Done | Phase 15 (#10) |
| 9 | Blank modal title sends no request | Submit New Task modal with empty title | Phase 15 (#12) |
| 10 | Server validation error keeps modal open | Edit a ToDo task's status straight to Done | Phase 15 (#13) |

No large refactor was performed in this build — the code was written once,
directly against the course spec, and verified incrementally phase by
phase rather than written messily and cleaned up afterward. Phase 18 below
is therefore a genuine final-quality pass (unused imports, temp files,
`git status`), not a behavior-changing refactor, so no additional
before/after contract re-run was needed beyond what Phase 18 already
records.
