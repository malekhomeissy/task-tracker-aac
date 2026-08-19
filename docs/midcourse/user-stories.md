# Mid-Course Project — User Stories

## Feature 1: Due Dates + Overdue Filter

**Story 1.** As a task owner, I want to set an optional due date on a task
so I know when it needs to be finished.
- Acceptance: `POST /tasks` accepts an optional `due_date` (ISO date). Tasks
  created without one still work exactly as before (`due_date` is `null`).
- Acceptance: an invalid date string returns a normal 422, the same way any
  other malformed field does.

**Story 2.** As a task owner, I want to change or clear a task's due date
after creating it, without affecting anything else about the task.
- Acceptance: `PATCH /tasks/{id}` with `{"due_date": "<date>"}` updates only
  the due date. `PATCH` with `{"due_date": null}` clears it. Omitting
  `due_date` entirely from a PATCH body leaves it untouched.

**Story 3.** As a task owner, I want overdue tasks to be visually obvious on
the board, so I don't miss deadlines.
- Acceptance: a task with a due date in the past and a status other than
  Done shows an "Overdue" badge and its due date in red on its card.
- Acceptance: a completed task never shows the Overdue badge, no matter how
  far in the past its due date is.

**Story 4.** As a task owner, I want to filter the board down to only
overdue tasks, so I can focus on what's late.
- Acceptance: checking "Overdue Only" calls `GET /tasks?overdue=true` and
  the board shows only tasks where `is_overdue` is true. Unchecking it
  restores the full board. A filter with no matches shows an empty board,
  not an error.

**Real AI-assumption correction (Feature 1):** the first draft of the
`is_overdue` logic checked only the due date against today's date and did
not check task status at all. This meant a task that was completed *after*
its due date passed would still show as overdue, which contradicts Story 3's
acceptance criteria directly. This was not caught by reading the code — it
was caught by `test_completed_past_due_task_is_not_overdue`, written from
Story 3, actually failing on the first real test run
(`assert True is False`). The fix added an explicit `status == Done` check
before the date comparison. See `docs/midcourse/verification.md`, Feature 1
section, for the exact command output.

---

## Feature 2: Tags/Labels

**Story 5.** As a task owner, I want to add a few short labels to a task
(like "backend" or "urgent") so I can categorize it without a whole tagging
system.
- Acceptance: `POST /tasks` and `PATCH /tasks/{id}` accept an optional
  `tags` list of strings. A task created with no `tags` field defaults to
  an empty list.

**Story 6.** As a task owner, I want the system to clean up my tag input a
little (trim stray spaces) but reject tags that are obviously wrong, so I
don't end up with junk labels.
- Acceptance: leading/trailing whitespace on each tag is trimmed
  automatically. A blank or whitespace-only tag is rejected with 422. A tag
  over 20 characters is rejected with 422. More than 5 tags on one task is
  rejected with 422; exactly 5 is allowed.

**Story 7.** As a task owner, I want my tags to stay on a task when I edit
something unrelated (like the description), so I don't have to re-enter them
every time.
- Acceptance: a PATCH that does not include `tags` in its body leaves the
  task's existing tags exactly as they were.

**Story 8.** As a task owner, I want to filter the board to tasks with a
specific tag, so I can see everything related to one area of work.
- Acceptance: `GET /tasks?tag=<value>` returns only tasks whose `tags` list
  contains that exact value. A tag with no matching tasks returns 200 and
  `[]`, not an error.

**Real design-time correction (Feature 2):** the spec for this feature was
written to intentionally avoid a separate `Tag` model or a tags table, but
the first instinct when sketching the data model out loud was to reach for
exactly that — a `Tag` entity with its own id/name and a many-to-many join
to tasks, "in case tags need colors or a management screen later." That
would have meant new storage structures, join logic, and cascading-delete
handling for a feature that only needs a list of short strings living on the
task itself. This was caught during planning, before any code was written,
specifically by rereading the feature's explicit constraints ("no separate
Tag model," "no tag management UI," "no tag DB table"). The simpler
`tags: List[str]` directly on `TaskResponse` was used instead. This
alternative and the reasoning for rejecting it are recorded in
`docs/midcourse/mini-adr.md`.

**Real bug found via tests (Feature 2):** the first draft of the max-5-tags
check used `len(value) >= MAX_TAGS`, which rejected a task with exactly 5
tags — one off from the actual rule ("at most 5"). Caught by
`test_create_task_with_exactly_five_tags_succeeds` failing for real
(`assert 422 == 201`) on the first test run. Fixed by changing the
comparison to `>`. See `docs/midcourse/verification.md`, Feature 2 section.
