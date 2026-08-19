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
- Docker or any deployment configuration
- Real-time sync, WebSockets, or notifications
- A frontend framework or build system (React, Vue, TypeScript, npm, etc.)

These are out of scope for Modules 1-3 by design — see Module 1's lecture
notes ("Task Tracker scope") for the course's own explanation of why.

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
`pytest tests/ -v` for the test suite (45 tests: 24 from the Modules 1-3
baseline, plus 9 for due dates and 12 for tags).

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
