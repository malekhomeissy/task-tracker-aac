# Security Review — Task Tracker

Read-only audit. No files outside `docs/` were changed to produce this
review. Every finding below cites the actual file and line evidence it is
based on — no generic OWASP filler.

Files inspected: `app/main.py`, `app/models.py`, `app/storage.py`,
`app/business_rules.py`, `tests/test_tasks.py`, `tests/conftest.py`,
`frontend/index.html`, `requirements.txt`, `Dockerfile`, `.dockerignore`,
`.github/workflows/ci.yml`, `AGENTS.md`, `README.md`.

---

## AI Findings

A first-pass, checklist-style audit across the standard categories
(unbounded fields, auth/ownership, client-trusted data, error leakage,
secrets, CORS, Docker/CI defaults, dependency risk).

| ID | Severity | File/location | Finding | Evidence | Risk | Grade | Why this grade | Next action |
|---|---|---|---|---|---|---|---|---|
| AI-1 | Medium | `app/models.py:71,93` (`description`) and `:74,96` (`assignee`) | `description` and `assignee` have no length limit, unlike `title` (200 chars) and each `tag` (20 chars) | Neither field has a `field_validator` or `Field(max_length=...)`; `title` has `MAX_TITLE_LENGTH = 200` enforced in `_validate_title`, tags have `MAX_TAG_LENGTH = 20`, but no equivalent exists for `description`/`assignee` | A client can `POST` a task with a multi-megabyte `description`, which is stored forever in the in-memory dict (`app/storage.py`'s `_tasks`) with no eviction | Valid | Real for this repo: two fields genuinely have no cap while sibling fields do, and the in-memory store has no persistence limit either | Add a `Field(max_length=...)` (or a validator matching the `_validate_title` pattern) to both fields |
| AI-2 | Medium | `app/main.py` (all `/tasks*` routes) | No authentication, authorization, or ownership checks on any task endpoint | Every route (`create_task`, `list_tasks`, `get_task`, `patch_task`, `delete_task`) takes no identity/credential parameter and `app/main.py` has no auth dependency anywhere | Any client that can reach the API can read, edit, or delete any task; there is no per-user ownership model at all | Valid | Accurately described as an intentional course-scope decision (`README.md`'s "Course scope" section lists "Authentication or user accounts" as explicitly out of scope), but the risk framing is still accurate if this were ever deployed beyond local course use | Documented here and in `README.md`; would need real auth before any non-course deployment |
| AI-3 | Low | `app/main.py:25-33` (`CORSMiddleware`) | `allow_methods=["*"]` and `allow_headers=["*"]` are wildcarded | `app.add_middleware(CORSMiddleware, allow_origins=[...two explicit localhost origins...], allow_methods=["*"], allow_headers=["*"])` | In general, wildcard methods/headers widen the CORS surface | False Positive | `allow_origins` is NOT wildcarded (only two explicit local dev origins), and `allow_credentials` is never set (defaults to `False` in Starlette), so no credentialed cross-origin request is possible regardless of the method/header wildcards — the actual exploitable surface this creates is negligible for this configuration | None — already effectively mitigated by the origin restriction |
| AI-4 | High | (claimed, not repo-specific) | "SQL injection risk in task queries" | — | — | False Positive | This project has no SQL anywhere — `app/storage.py` is a plain Python dict (`_tasks: dict[str, TaskResponse] = {}`), there is no database driver in `requirements.txt`, and no query string is ever constructed from user input. This finding is included deliberately as an example of a plausible-sounding but repo-inaccurate claim, per the course's guidance on grading AI output rather than accepting it | None — the finding does not apply |
| AI-5 | Info | (claimed, not repo-specific) | "Validate all input more thoroughly" | — | — | Noise | Technically true of almost any API but not actionable without naming a specific field, route, or failure mode — this project already validates title, tags, status, priority, and due_date with specific, testable rules (see `app/models.py`); a generic "validate more" comment adds nothing beyond AI-1's specific finding | None — superseded by AI-1, which names the actual gap |
| AI-6 | Low | `requirements.txt` | Dependencies are unpinned (`>=` lower bounds only, no upper bounds, no lockfile) | `fastapi>=0.110`, `uvicorn[standard]>=0.29`, `pydantic>=2.6`, `pytest>=8.0`, `httpx>=0.27` — every line uses `>=`, none uses `==` or a hash | A `pip install -r requirements.txt` run today vs. in six months can silently resolve to different (potentially vulnerable or breaking) versions, and the Docker image (`docker build`) is not reproducible | Valid | Real and concrete: the file genuinely has no upper bounds or lockfile, and this directly affects both local installs and the Docker build | Consider pinning exact versions or adding a lockfile (e.g. `pip-compile`) before any real deployment |
| AI-7 | Low | `Dockerfile` (both `COPY requirements.txt .` lines) | The production image installs test-only dependencies (`pytest`, `httpx`) because `requirements.txt` is not split into runtime vs. dev/test dependencies | `requirements.txt` has one file for both; `Dockerfile`'s builder stage runs `pip install -r requirements.txt` unconditionally, and `pytest`/`httpx` are never excluded from the runtime image | Slightly larger image, more installed packages than the running app needs, marginally larger dependency-vulnerability surface | Valid | Real and minor: confirmed by reading both files directly — there genuinely is no `requirements-runtime.txt` split | Split into `requirements.txt` (runtime) and `requirements-dev.txt` (test/dev), and have the Dockerfile install only the former |
| AI-8 | Info | `.github/workflows/ci.yml` | GitHub Actions are pinned by tag (`actions/checkout@v4`, `actions/setup-python@v5`), not by commit SHA | Both `uses:` lines reference a version tag, not a SHA | A tag can be moved by the action's maintainer (or, in a supply-chain-attack scenario, by a compromised account) to point at different code without the workflow file changing | Valid | Real, standard supply-chain hardening advice that does apply to this exact file, though low severity for a course project with no secrets in CI | Optional hardening: pin to a commit SHA if this repo ever needs stronger supply-chain guarantees |

---

## My Manual Findings

Findings from an independent, judgment-driven pass — not a re-listing of
the table above. These are the kind of things a keyword-style scan is
unlikely to surface on its own.

**M-1 — Read-modify-write race in `update_task` (Low severity, Valid).**
`app/storage.py`'s `update_task` does `existing = _tasks.get(task_id)`,
computes `updated` from it, then later does `_tasks[task_id] = updated`.
Every route in `app/main.py` is defined with plain `def`, not `async def`
(verified: `def create_task`, `def list_tasks`, `def get_task`,
`def patch_task`, `def delete_task`), which means FastAPI runs each one in
a worker thread pool, not on the single asyncio event loop. Two concurrent
`PATCH` requests to the *same* task could both read the same `existing`
value before either writes back, so one update could silently overwrite
the other (a classic lost-update race). This is a real gap, but a narrow
one — it requires two concurrent PATCH requests to the exact same task id,
which is unlikely in the course's single-user local-dev usage pattern. I'm
grading it Valid (it is real and the mechanism is concretely traceable in
the code) but ranking it below the top-3 backlog items because the actual
likelihood of a real collision here is low for this project's usage.

**M-2 — Verified server-managed fields cannot be spoofed by a client
(checked, found nothing new).** `id`, `created_at`, `updated_at`, and
`is_overdue` are never accepted from client input — they don't exist as
fields on `TaskCreate` or `TaskUpdate` at all (only on `TaskResponse`), and
both request models use `model_config = ConfigDict(extra="forbid")`, so a
client attempting to POST `{"id": "fake-id", ...}` or
`{"created_at": "...", ...}` gets a 422 for the unknown field rather than
having it silently accepted. I checked this directly by reading both model
classes and confirming the field lists don't overlap; I did not find a way
around it.

**M-3 — Verified the frontend's HTML-escaping is applied consistently
(checked, found nothing new).** Every place `frontend/index.html` builds
`card.innerHTML` or `header.innerHTML` from task data — `task.title`,
`task.description`, `task.priority`, `task.assignee`, `task.due_date`,
each entry in `task.tags`, and `task.id` — passes through the same
`escapeHtml()` helper (confirmed by grepping every `.innerHTML =` /
`.innerHTML +=` assignment in the file and checking each interpolated
value). Every place that sets plain text (error banners, status messages)
uses `.textContent`, which needs no escaping. I did not find a reflected-
XSS gap in the card-rendering or error-display code paths.

**M-4 — CI triggers on every push to every branch, not just `main`
(design note, not a security finding).** `.github/workflows/ci.yml`'s
`push:` trigger has no branch filter, so every push anywhere runs the full
test suite. This isn't a security risk, but it is a cost/design choice
worth naming: it satisfies the brief's "runs on push and pull request"
requirement in the simplest possible way, at the cost of running CI on
every branch push rather than only `main`/PRs.

**M-5 — Checked Docker image contents against `.dockerignore` (checked,
found nothing new).** Traced exactly what ends up in the final image:
the runtime stage's only `COPY` instructions are `COPY --from=builder
/opt/venv /opt/venv` and `COPY app/ ./app/`. `frontend/`, `tests/`,
`docs/`, `.git`, and any `.env` file are never copied in the first place —
`.dockerignore` is actually redundant with the Dockerfile's own narrow
`COPY` list here, but having both is a reasonable belt-and-suspenders
approach, not a gap.

**M-6 — `description` can be explicitly set to `null` via PATCH, the same
class of bug as the facilitator-reported null-title issue, but it was
never fixed (Low-Medium severity, Valid).** Found while reviewing the
null-title fix diff (`002b58a`) for `docs/final-ai-review.md`'s code
review mini-log: that fix only guards `TaskUpdate.title`, and
`description` has no equivalent guard (`app/models.py`:
`description: Optional[str] = None` on `TaskUpdate`, with no
`field_validator` at all). Confirmed live against a running instance of
the app, not just by reading the code:

```
$ curl -s -i -X PATCH http://localhost:8010/tasks/{id} \
    -H 'Content-Type: application/json' -d '{"description": null}'
HTTP/1.1 200 OK
{"id":"...","description":null, ...}

$ curl -s -i http://localhost:8010/tasks/{id}
HTTP/1.1 200 OK
{"id":"...","description":null, ...}
```

`TaskResponse.description` is typed as a plain `str` (not `Optional[str]`)
— exactly the same type contract `title` has — so this PATCH request
persists a value that violates the response model's own declared type,
the same shape of bug the facilitator caught for `title`. (By contrast,
`assignee` is genuinely `Optional[str]` on `TaskResponse` too, so an
explicit `{"assignee": null}` is correct, expected behavior, not a bug —
confirmed the same way, live, and excluded from this finding.) This
extends AI-1's "no length cap" finding with a more specific and more
severe angle AI-1 didn't name: it isn't just unbounded, it's exposed to
the exact class of defect that was already fixed once for a sibling
field. Not fixed here — per the Module 5/final-project boundary
(`AGENTS.md`, "no unjustified `app/` edits" and this document's own
read-only scope), this is recorded as a finding for the repo owner to
decide on, using the existing `title` fix in commit `002b58a` as the
direct template if it's addressed.

---

## Reconciliation

**Agreement** (both passes independently flagged the same underlying
issue, from different angles):
- Unbounded input (AI-1: missing length caps on `description`/`assignee`)
  and the in-memory storage model together point at the same underlying
  risk category — unbounded resource growth — that M-1's race-condition
  finding also touches on structurally (both are about `app/storage.py`
  having no safeguards around concurrent/unbounded writes).

**AI-only** (surfaced by the checklist pass, not independently found in
the manual pass): AI-2 (no auth), AI-3 (CORS wildcard methods/headers,
graded False Positive), AI-4 (SQL injection claim, graded False Positive),
AI-5 (generic "validate more", graded Noise), AI-6 (unpinned dependencies),
AI-7 (test deps in prod image), AI-8 (Actions pinned by tag not SHA).

**You-only** (found by reading the actual execution model and code paths,
not by scanning for a category): M-1 (the threadpool race condition — this
required knowing that plain `def` routes run in a worker thread pool in
FastAPI, not just reading the file for keywords), M-2, M-3, and M-5 (all
three are "I checked this specific thing and it holds up" verifications,
which a category-scan naturally doesn't produce since there's no
"finding" to report when something turns out fine), and M-6 (found by
comparing the null-title fix's actual diff scope against the rest of
`TaskUpdate`'s fields and confirming the gap live against a running
instance — the AI checklist pass's AI-1 named the general unbounded-field
category but did not independently spot this more specific, same-class-as-
the-facilitator-bug angle).

The You-only column is where this review's actual judgment shows up most:
M-1 needed framework-execution-model knowledge beyond the code itself, and
M-2/M-3/M-5 are the kind of "I verified this concern doesn't apply"
checks that only happen when someone deliberately goes looking for a
specific failure mode and doesn't find it — a checklist audit tends to
only report what it flags, not what it checked and ruled out.

---

## Top-3 Security Backlog

Ranked by real-world severity among the Valid findings, not just by table
order.

**1. No authentication/authorization on task endpoints (AI-2).**
Why it matters: every task-mutating route is open to anyone who can reach
the API — for a course project this is an accepted, documented scope
decision, but it's the single highest-impact gap if this code were ever
reused as a starting point for something real. Suggested owner: whoever
extends this project past the course (a future "add auth" module).
Concrete next action: before any non-course deployment, add a minimal
auth dependency (e.g. an API key or session check) to every `/tasks*`
route in `app/main.py`, and add an `owner`/`created_by` field so ownership
checks are possible.

**2. Unbounded `description`/`assignee` fields with no storage cap
(AI-1).** Why it matters: combined with no authentication (item 1) and no
per-request or total-task-count limit anywhere in `app/storage.py`, a
single client could grow the in-memory dict without bound, which for a
single-process, single-dict store is a direct memory-exhaustion path.
Suggested owner: whoever next touches `app/models.py`. Concrete next
action: add `Field(max_length=...)` to `description` (e.g. 2000 chars,
matching the course's own comment-body precedent from the Module 5
comments-feature plan) and to `assignee` (e.g. 100 chars), following the
exact pattern already used for `title` (`_validate_title`) and `tags`
(`_validate_tags`).

**3. Unpinned dependencies across `requirements.txt`, the Docker build,
and GitHub Actions (AI-6, AI-7, AI-8 combined).** Why it matters: none of
these are severe individually, but together they mean neither a local
`pip install`, a `docker build`, nor a CI run is fully reproducible, and a
new vulnerable transitive dependency could enter silently on any of the
three paths. Suggested owner: whoever owns release engineering for this
project going forward. Concrete next action: pin `requirements.txt` to
exact versions (or add a lockfile), split it into runtime vs. dev/test
requirements so the Docker image only installs what it runs, and pin the
two GitHub Actions in `.github/workflows/ci.yml` to commit SHAs.

This backlog is not implemented as part of this review — per the Module 5
boundaries in `AGENTS.md`, this document records findings; it does not
fix them.
