# Architecture — Strategy A: Minimal Context

**Context given to produce this document:** a single line — "This is the
Task Tracker project, a FastAPI-based task management app used for an
AI-assisted coding course." No files were read. No `AGENTS.md`, no source
code, nothing else. This document is written the way an AI would answer if
asked to describe the architecture from that one sentence alone.

## Assumed architecture

- **Backend:** a FastAPI application, almost certainly backed by a
  relational database (PostgreSQL or SQLite are the most common defaults
  for a project like this) accessed through an ORM such as SQLAlchemy.
- **Auth:** task trackers used in a course context typically include basic
  user accounts, so there is probably a login/registration flow and
  per-user task ownership, likely using JWT or session cookies.
- **Data model:** a `Task` entity with the fields you'd expect from any
  task tracker — title, description, status, maybe priority, maybe a due
  date — and probably a `User` entity it belongs to.
- **Frontend:** given it's a course project built in 2025-2026, the
  frontend is likely a modern JS framework such as React, with a build
  step (Vite or similar), rather than plain HTML/JS.
- **Tests:** some kind of automated test suite, most likely pytest for the
  backend, though the exact scope is unknown.
- **Deployment:** possibly containerized with Docker; CI is a common
  addition for a course that emphasizes AI-assisted engineering practice,
  but this is a guess.

## What was generic (boilerplate assumptions, not specific to this repo)

- "FastAPI + SQLAlchemy + JWT auth" is close to the default mental
  template for *any* FastAPI CRUD tutorial, not something this one-line
  description actually supports.
- "Some kind of automated test suite" is true of almost every course
  project and carries no real information.

## What was inferred (reasoned from the one sentence, but not verified)

- That there's a `Task` entity with common task-tracker fields — inferred
  from the project's name, not from any actual field list.

## What was invented (stated with no basis at all, and — checked against
the real repo — turned out to be wrong)

- **A relational database and an ORM.** The real project (confirmed in
  Strategy C and B below) uses a single in-memory Python dictionary with
  no persistence at all. This is the single biggest miss in this document.
- **User accounts / auth / JWT.** The real project has no auth system
  whatsoever — confirmed by `requirements.txt` containing no auth library
  at all, and every route in `app/main.py` being open with no
  authentication dependency.
- **A React frontend with a build step.** The real project is a single
  vanilla HTML/CSS/JS file with no build step at all
  (`frontend/index.html`).
- **A `User` entity.** Does not exist anywhere in this codebase.

This document is a reasonable *starting guess* for "some FastAPI project,"
and is a useful illustration of exactly how much a minimal-context answer
gets wrong about a *specific* codebase — every one of its four biggest
claims (database, auth, frontend framework, user entity) is incorrect for
this repo.
