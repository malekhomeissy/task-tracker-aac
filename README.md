# Task Tracker — AI-Assisted Coding Modules 1-3 Baseline

This repository is the Modules 1-3 Task Tracker baseline for AUB's
AI-Assisted Coding course. It reconstructs the project as described in the
official Module 1, Module 2, and Module 3 lecture notes and prompt
libraries: a FastAPI backend with in-memory storage and status-transition
business rules, a pytest suite, and a vanilla HTML/CSS/JS Kanban frontend.
It intentionally stops at the scope those three modules describe so it's
ready as the starting point for the mid-course project.

## Project structure

```
task-tracker/
├── app/
│   ├── main.py            # FastAPI app: /health + 5 CRUD routes
│   ├── models.py          # Pydantic v2 models and enums
│   ├── storage.py         # in-memory storage
│   └── business_rules.py  # status-transition validation
├── frontend/
│   └── index.html         # vanilla HTML/CSS/JS Kanban board
├── tests/
│   ├── conftest.py
│   ├── test_tasks.py      # pytest API tests
│   └── verify_a.py        # standalone Module 2 model verification script
├── docs/
│   ├── baseline-build-log.md
│   └── midcourse/          # Mid-Course Project docs (see below)
├── requirements.txt
└── README.md
```

## Setup

Create and activate a virtual environment (optional but recommended), then
install dependencies:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: `curl http://localhost:8000/health`
- Interactive API docs (Swagger UI): http://localhost:8000/docs

Storage is intentionally **in-memory only** — all tasks are lost whenever
the backend process restarts. This is a deliberate simplification for the
Modules 1-3 learning project, not an oversight.

## Run the frontend

The frontend is a single static file with no build step. Serve it from the
`frontend/` folder with any static file server, for example:

```bash
cd frontend
python -m http.server 5500
```

Then open **http://localhost:5500/index.html** in a browser, with the
backend already running on port 8000 in another terminal.

> The backend allows CORS requests from `http://localhost:5500` and
> `http://127.0.0.1:5500` specifically, since that's the origin used above.
> If you serve the frontend from a different port, add that origin to the
> `CORSMiddleware` configuration in `app/main.py`.

## Run model verification (Module 2)

A standalone script independently checks 8 behaviors of the Pydantic
models without pytest:

```bash
python -m tests.verify_a
```

Every line should print `PASS`.

## Run the test suite

```bash
pytest tests/ -v
```

## Manual verification steps

Most of Module 3's frontend behaviors were verified with an automated
headless-browser script during development (see
`docs/baseline-build-log.md`, Phase 15, for the full evidence). A few
things are genuinely easier to eyeball than to automate — if you want to
double-check the app yourself, with the backend on `:8000` and the
frontend served on `:5500`:

- General visual polish (spacing, colors, layout on your own screen size).
- Dragging a card with an actual mouse (the automated check dispatches the
  same drag/drop events a real drag produces, but isn't literally a mouse
  movement).

## Course scope

This baseline intentionally does **not** include:

- Authentication or user accounts
- A database (storage is in-memory only)
- Real-time sync, WebSockets, or notifications
- A frontend framework or build system (React, Vue, TypeScript, npm, etc.)

These are out of scope for Modules 1-3 by design — see Module 1's lecture
notes ("Task Tracker scope") for the course's own explanation of why. (A
Docker image and a CI workflow were added later, in the Final Project —
see below; they wrap this same in-memory, auth-less baseline rather than
changing it.)

## Mid-Course Project

Branch `mid-course-project` builds two scoped features on top of the
Modules 1-3 baseline above, without changing its architecture:

- **Due Dates + Overdue Filter** — an optional `due_date` on each task, an
  `is_overdue` flag derived on every read (never stored) from `due_date` and
  `status`, and an `overdue` filter on `GET /tasks`. Completed tasks are
  never overdue. The frontend adds a due-date field to the create/edit
  modal, a due date + Overdue badge on cards, and an "Overdue Only" filter
  checkbox.
- **Tags/Labels** — an optional `tags: List[str]` on each task (max 5 tags,
  max 20 characters each, trimmed, blank tags rejected), stored directly on
  the task with no separate tag model or table, plus a `tag` filter on
  `GET /tasks`. The frontend adds a comma-separated tags field to the modal,
  tag chips on cards, and a compact tag filter input.

Both features preserve all existing Modules 1-3 behavior: layout, status
columns, priority sorting, drag-and-drop, the status-transition business
rules, and modal validation/error handling are all unchanged.

### Running it

Same commands as above — `uvicorn app.main:app --reload --port 8000` for the
backend, `python -m http.server 5500` from `frontend/` for the frontend,
`pytest tests/ -v` for the test suite (46 tests: 24 from the Modules 1-3
baseline, 9 for due dates, 12 for tags, plus 1 regression test added for a
facilitator-reported fix — see `docs/midcourse/verification.md`).

### Documentation

The full AI-assisted workflow for this project — user stories, an ADR for
the due-date/tag design decisions, a prompt log (including a weak-vs-strong
prompt rewrite exercise), a verification log with real command output and
two Break Tests, and a reflection — lives in `docs/midcourse/`:

```
docs/midcourse/
├── user-stories.md
├── mini-adr.md
├── prompt-log.md
├── verification.md
└── reflection.md
```

## Final Project

Branch reviewed: `final-project`

### What this submission demonstrates

- The existing Task Tracker app still runs inside the intended course
  scope — no new product features, no changes to `app/`'s behavior.
- CI (`.github/workflows/ci.yml`) runs the pytest suite on every push and
  on pull requests targeting `main`.
- A `Dockerfile`/`.dockerignore` are in place for a non-root, multi-stage
  image that serves `/health`. The image was built and run on macOS,
  `/health` returned HTTP 200, and `docker exec tt-dev whoami` returned
  `app`; the exact commands and results are recorded in
  `docs/release-evidence.md`.
- AI review, security, governance, and ownership evidence all live under
  `docs/` (see "Evidence files" below).

### How to run locally

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### How to run tests

```bash
pytest tests/ -v
```

### How to run with Docker

```bash
docker build -t task-tracker:dev .
docker run --rm -d -p 8000:8000 --name tt-dev task-tracker:dev
curl -i http://localhost:8000/health
```

### Evidence files

- `docs/release-evidence.md`
- `docs/final-ai-review.md`
- `docs/security-review.md`
- `docs/governance-worksheet.md`
- `docs/ai-usage.md`
- `docs/ai-playbook.md`
- `docs/decisions/comments-feature-plan.md`
- `docs/architecture.md` (with `architecture-A.md`/`-B.md`/`-C.md`)

### AI assistance summary

AI helped draft or review: CI workflow, Dockerfile, documentation
(`docs/`), security review, and the facilitator-reported null-title
debugging fix.

I verified the work by: running the full pytest suite before and after
each change, reading every generated file against the actual repo instead
of trusting the draft, curling the running backend to check real status
codes and behavior, and grading every AI-produced finding/comment
(Valid/False Positive/Noise; Useful/Noise/Wrong) instead of accepting it.

One AI suggestion I rejected or corrected: an AI code-review comment
noted that `description` has the same unguarded-explicit-null gap that
the facilitator caught for `title`, and the natural next step would have
been to apply the same one-line fix. I chose not to apply it in this pass
— it's recorded as finding M-6 in `docs/security-review.md` instead —
because this project's ground rules scope `app/` changes to what's
already explained and explicitly decided on, not whatever an AI review
happens to notice along the way. Full reasoning in
`docs/final-ai-review.md`.
