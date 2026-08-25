# Release Evidence

Real commands and real output only. Docker runtime verification was completed
manually on the project owner's Mac. The only evidence still dependent on a
remote service is the GitHub Actions run, which can exist only after the
`final-project` branch is pushed.

## Baseline

- Branch: `final-project` (branched from `mid-course-project` at commit
  `002b58a`, which already includes the Modules 1-4 baseline, both
  mid-course features, and the facilitator-reported null-title fix)
- Date: 2026-08-25
- Local app run command: `uvicorn app.main:app --reload --port 8000`
- `/health` result:
  ```
  $ curl -s -i http://localhost:8000/health
  HTTP/1.1 200 OK
  content-type: application/json

  {"status":"ok","timestamp":"2026-08-25T11:22:04.243701+00:00"}
  ```
- Frontend check: served `frontend/index.html` with
  `python -m http.server 5500` from the `frontend/` folder, then opened it
  in headless Chromium via Playwright (`/tmp/frontend_baseline_check.py`)
  against the running backend. Confirmed programmatically: the three
  Kanban columns render with the correct labels
  (`['To Do', 'In Progress', 'Done']`), and clicking "+ New Task" opens the
  create-task modal (`#modal-overlay` becomes visible). Screenshot saved at
  `/tmp/frontend_baseline.png` during this session. The Kanban board and
  create/edit flow are still visible and functional.
- Test command: `pytest tests/ -v`
- Test result:
  ```
  ======================== 46 passed, 2 warnings in 0.39s ========================
  ```
  All 46 tests pass (24 Modules 1-3 baseline + 9 due-date + 12 tags + 1
  null-title regression test). No pre-existing failures, nothing skipped.

## CI evidence

- Workflow file: `.github/workflows/ci.yml`

### GitHub Actions verification

The `final-project` branch was pushed to the public GitHub repository and triggered the configured CI workflow.

GitHub Actions run **CI #1** for commit `539c4cf` ("Record verified Docker and final release evidence") completed successfully on the `final-project` branch in 14 seconds. The workflow installed the project dependencies and ran the pytest suite as configured in `.github/workflows/ci.yml`.

Result: **PASS** — GitHub Actions CI completed successfully.

## Docker evidence

Manual runtime verification was completed on the project owner's Mac on
2026-08-25 using Docker Desktop. The commands below are the commands that
were actually run.

- Docker version: `Docker version 29.7.2, build a7dcaa6`
- Build command: `docker build -t task-tracker:dev .`
  - Result: **PASS** — the image built successfully and was tagged
    `task-tracker:dev`.
- Run command:
  `docker run --rm -d -p 8000:8000 --name tt-dev task-tracker:dev`
  - Result: **PASS** — Docker returned a container ID and started the
    container.
- `/health` check: `curl -i http://localhost:8000/health`
  - Result: **PASS** — `HTTP/1.1 200 OK`, served by Uvicorn with an
    `application/json` body containing `{"status":"ok", ...}`.
- Non-root check: `docker exec tt-dev whoami`
  - Result: **PASS** — output was `app`, not `root`.
- Cleanup: `docker stop tt-dev`
  - Result: **PASS** — output was `tt-dev`.
- No-baked-secrets check: `.dockerignore` excludes `.env`, `.env.*`,
  `*.pem`, `*.key`, `.git`, `venv/`, `.venv/`, caches, and local build
  artifacts. The Dockerfile copies only `requirements.txt` and `app/` into
  the image.
- Runtime safety check: the Dockerfile uses an explicit Python 3.11 slim
  base, creates a dedicated `app` user, switches to `USER app` before the
  final command, and runs Uvicorn without `--reload`.

These checks satisfy the course runtime verification requirement: the image
builds, the container runs, `/health` responds with HTTP 200, and the process
runs as the non-root `app` user.

## Documentation claim-vs-reality log

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| `POST /tasks` returns `201 Created` on success | `curl -i -X POST http://localhost:8000/tasks -d '{"title":"Claim check task"}'` against the running backend | Confirmed: `HTTP/1.1 201 Created`, matching `status_code=status.HTTP_201_CREATED` in `app/main.py`'s `create_task` route | None needed |
| `DELETE /tasks/{id}` returns `204 No Content` with an empty body | `curl -i -X DELETE http://localhost:8000/tasks/{id}` against a real task's id, then re-checked the existing test `test_delete_existing_returns_204_no_body` in `tests/test_tasks.py` | Confirmed: `HTTP/1.1 204 No Content`, no response body, matching both the route's `status.HTTP_204_NO_CONTENT` and the existing test's `assert response.content == b""` | None needed |
| A blank/whitespace-only title returns `422`, not `400` or `500` | `curl -i -X POST http://localhost:8000/tasks -d '{"title":"   "}'` against the running backend | Confirmed: `HTTP/1.1 422 Unprocessable Entity`, matching Pydantic's default validation-error status code and the existing test `test_create_task_blank_title_returns_422` | None needed |

All three checks confirmed the existing documentation/code claims were
already accurate — no README or code correction was required as a result
of this pass.
