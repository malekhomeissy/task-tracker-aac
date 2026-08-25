# Release Evidence

Real commands and real output only. Two items in this document could not be
executed directly by the AI agent in the environment it had access to, and
that limitation is recorded honestly below rather than faked — see
"Environment limitations" at the end.

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
- Latest run link or note: **not available yet.** The AI agent working in
  this session does not have push access to
  `github.com/malekhomeissy/task-tracker-aac` (confirmed directly: a
  `git push --dry-run` from the session's own git credential was rejected
  by the git proxy with `access denied ... task-tracker-aac is not in this
  session's authorized repository set`), so no commit from this session has
  reached GitHub yet and no Actions run exists to link. Once `final-project`
  is pushed (see the final report for exact push instructions), the first
  push will trigger this workflow automatically — check
  `github.com/malekhomeissy/task-tracker-aac/actions` and paste the green
  run URL here.
- Test command used by CI: `pytest tests/ -v` (same command as the local
  baseline above — verified by reading `.github/workflows/ci.yml` directly,
  not by assumption).
- Shortcut check (verified by reading the actual workflow file):
  - No `continue-on-error` anywhere in the file.
  - No `|| true` anywhere in the file.
  - No `--exit-zero` or similar force-success flag.
  - Python version is pinned explicitly to `"3.11"`, not `latest`.
  - Dependency installation (`pip install -r requirements.txt`) runs before
    `pytest`, so missing test dependencies (`pytest`, `httpx`) aren't a
    silent no-op.
  - Triggers are `push` (all branches) and `pull_request` to `main`, so the
    workflow runs on both push and PR as required.

## Docker evidence

- Build command: `docker build -t task-tracker:dev .`
- Run command:
  `docker run --rm -d -p 8000:8000 --name tt-dev task-tracker:dev`
- `/health` check: `curl -i http://localhost:8000/health` (expect `200`)
- Non-root check: `docker exec tt-dev whoami` (expect `app`, not `root`) —
  the Dockerfile creates a dedicated `app` user (`useradd --create-home
  --shell /usr/sbin/nologin app`), `chown`s `/app` to it, and runs
  `USER app` before the final `CMD`.
- No-baked-secrets check: `.dockerignore` explicitly excludes `.env`,
  `.env.*`, `*.pem`, `*.key`, `.git`, and both virtualenv directory names
  (`venv/`, `.venv/`). The image's `COPY` instructions only copy
  `requirements.txt` and `app/` — `frontend/`, `tests/`, and `docs/` are
  never copied into the image at all (verified by reading the `Dockerfile`
  directly: it has exactly two `COPY` instructions, `COPY requirements.txt
  .` in the builder stage and `COPY app/ ./app/` in the runtime stage).

**Environment limitation — Docker build/run could not be executed by the
AI agent:** the cloud workspace this session ran in has the `docker` CLI
installed but no reachable Docker daemon (`docker info` errors with
`failed to connect to the docker API at unix:///var/run/docker.sock ...
no such file or directory`, and starting the daemon failed with
`ulimit: error setting limit (Operation not permitted)` — the sandbox does
not have the privileges to run a Docker daemon). The device bridge to your
Mac runs commands inside an isolated VM that does not have `docker` on its
`PATH` at all (`docker: command not found`), even though Docker Desktop may
be installed and running on your actual Mac outside that VM. So the four
commands above were not run against a real container in this session —
they are the exact commands to run, verified against what the Dockerfile
and `.dockerignore` actually contain, not evidence of an actual run.
**Please run the four commands above yourself in a real terminal on your
Mac** (not through this session) and record the actual output in this
section before considering the final project fully evidence-complete.

## Documentation claim-vs-reality log

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| `POST /tasks` returns `201 Created` on success | `curl -i -X POST http://localhost:8000/tasks -d '{"title":"Claim check task"}'` against the running backend | Confirmed: `HTTP/1.1 201 Created`, matching `status_code=status.HTTP_201_CREATED` in `app/main.py`'s `create_task` route | None needed |
| `DELETE /tasks/{id}` returns `204 No Content` with an empty body | `curl -i -X DELETE http://localhost:8000/tasks/{id}` against a real task's id, then re-checked the existing test `test_delete_existing_returns_204_no_body` in `tests/test_tasks.py` | Confirmed: `HTTP/1.1 204 No Content`, no response body, matching both the route's `status.HTTP_204_NO_CONTENT` and the existing test's `assert response.content == b""` | None needed |
| A blank/whitespace-only title returns `422`, not `400` or `500` | `curl -i -X POST http://localhost:8000/tasks -d '{"title":"   "}'` against the running backend | Confirmed: `HTTP/1.1 422 Unprocessable Entity`, matching Pydantic's default validation-error status code and the existing test `test_create_task_blank_title_returns_422` | None needed |

All three checks confirmed the existing documentation/code claims were
already accurate — no README or code correction was required as a result
of this pass.
