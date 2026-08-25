# Architecture — Final (Synthesized from Three Context Strategies)

This document is the actual, verified architecture description for this
project, built by taking the best-verified material out of
`docs/architecture-A.md`, `docs/architecture-B.md`, and
`docs/architecture-C.md` and cross-checking every claim against the full
repository (all of `app/`, `frontend/`, `tests/`, `AGENTS.md`, and the
config/CI files) rather than the restricted context each of those three
documents was limited to.

## System overview

The Task Tracker is a FastAPI backend (`app/main.py`) with an in-memory
store (`app/storage.py`, a single module-level `dict`, no database, no
persistence across restarts), five CRUD routes plus `/health`, Pydantic
v2 request/response models (`app/models.py`), and a separate
status-transition rules module (`app/business_rules.py`) that gates
`PATCH` status changes to a fixed set of legal transitions
(`ToDo→InProgress`, `InProgress→Done`, `Done→InProgress`; anything else,
including same-status, is a 422). The frontend
(`frontend/index.html`) is a single vanilla HTML/CSS/JS file — no build
step, no framework — rendering a three-column Kanban board with
drag-and-drop and one shared modal for both creating and editing a task.
There is no authentication anywhere in the system, which `AGENTS.md`
documents as an intentional course-scope decision. The test suite
(`tests/test_tasks.py`, 46 tests as of this branch) covers CRUD,
validation, status transitions, due dates, and tags. CI
(`.github/workflows/ci.yml`) and a Docker build
(`Dockerfile`/`.dockerignore`) were added in this Module 5 pass and are
not part of the Modules 1-4 baseline any of the three context strategies
were tested against.

One correction worth calling out explicitly: `description` and
`assignee` have no length cap or blank-rejection validator at all,
unlike `title` and `tags` — this is a real, currently-unaddressed gap,
tracked as finding AI-1 in `docs/security-review.md`, not a design
decision.

## Comparison log

| | Strategy A (minimal) | Strategy B (structured: AGENTS.md + summaries) | Strategy C (targeted: 3 anchor files, raw) |
|---|---|---|---|
| **Right** | Correctly guessed "FastAPI" and "pytest" (both given away by the one-line prompt itself). | Correctly identified no database, no auth, vanilla-JS frontend, the five routes, the computed `is_overdue` field, and the existence of a separate business-rules module — everything Strategy A invented, this one got right. | Every claim it made is directly verifiable against `app/main.py`/`app/models.py`/`app/storage.py` — CORS origins, exact validation caps, PATCH's `exclude_unset` partial-update semantics, all correct. |
| **Wrong** | Database/ORM, auth/JWT, React frontend, `User` entity — all four invented and all four incorrect. | The extrapolated claim that `description`/`assignee` share `title`/`tags`'s validation — plausible-sounding, stated with confidence, and false. | Nothing stated was wrong — the strategy's discipline (only claim what's in the three files) meant it had no wrong claims, only gaps. |
| **Missed** | Almost everything specific to this repo — no route list, no field list, no mention of the in-memory store, no business-rules module. | Didn't surface the CORS origin restriction or the PATCH `exclude_unset` partial-update mechanic, since the file summaries it worked from didn't include that level of detail. | Everything outside the three files by design: frontend behavior, test coverage, the actual status-transition rules (only that the module exists), CI/Docker, `AGENTS.md`'s stated project boundaries. |
| **Invented** | Database engine, auth mechanism, frontend framework, `User` entity — see above. | The description/assignee validation claim (see "Wrong"). | Nothing — this strategy's defining trait is that it invented nothing, at the cost of covering less ground. |

- **Most accurate:** Strategy C. Every factual claim it makes is directly
  traceable to one of the three files it read, with zero invented or
  extrapolated details.
- **Most honest:** Strategy C, for the same reason — it explicitly lists
  what it cannot speak to instead of guessing, which is the property that
  actually matters when someone downstream is going to trust the
  document.
- **Best for onboarding:** Strategy B. A new contributor needs the whole
  system in one pass — frontend, backend, tests, business rules — and
  Strategy B is the only one of the three that covers all of it, even
  though its one extrapolated claim needed a correction. For onboarding,
  breadth-with-one-flagged-error beats narrow-but-perfect or
  broad-but-wrong.
- **Best for security review:** Strategy C as a starting discipline, but
  not sufficient alone — the actual `docs/security-review.md` produced
  for this project had to also read `frontend/index.html` (for XSS
  patterns), `.github/workflows/ci.yml` and `Dockerfile` (for
  supply-chain/deployment findings), none of which are among Strategy C's
  three anchor files. The lesson isn't "use Strategy C for security
  review," it's "use Strategy C's *discipline* (verify every claim
  against a real file, mark what you haven't checked) and apply it to
  every file the review actually needs, not just three."
- **Best for feature planning:** Strategy B's breadth plus Strategy C's
  verification habit — which is exactly the two-pass structure
  `docs/decisions/comments-feature-plan.md` used: a broad first plan,
  then a grounded pass that read the real anchor files and corrected two
  wrong assumptions (no database, no separate detail page) before writing
  the final plan.

## The rule

For any task that produces a document someone else will trust as fact
about this repo — security review, feature planning, onboarding — I use
targeted context (Strategy C) or Strategy C's verification discipline
applied to whatever broader file set the task actually needs, because
this codebase is small enough that reading the real files costs almost
nothing and it eliminates the kind of confidently-wrong extrapolation
Strategy B produced. I reach for minimal context (Strategy A) only as a
five-minute gut-check before doing real work, never as something I'd
hand to someone else, because it visibly guessed wrong about the three
facts that matter most about this project: storage, auth, and the
frontend stack.
