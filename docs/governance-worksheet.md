# Governance Worksheet

This is a retrospective on how AI was actually used across this project,
grounded in the real git history, the real prompt logs in
`docs/midcourse/`, and this session's own record of what I gave the AI
agent access to for the Module 5 / final-project work. Nothing here is
invented — every row either cites a commit, a file, or an event from this
session.

## What I Shared With AI

Risk key (as defined for this exercise): **Low** = public/toy/course-only
data, no secrets; **Medium** = private but non-sensitive code or project
details; **High** = credentials, tokens, secrets, PII, real customer data,
production logs, or private production config.

| Item shared | Risk | Reason | Safer approach for next time |
|---|---|---|---|
| Full contents of `app/models.py`, `app/main.py`, `app/storage.py`, `app/business_rules.py` (Modules 1-4 and this session) | Low | This is a course toy project in a public GitHub repo (`malekhomeissy/task-tracker-aac`). There is no real user data, no database, and no secrets anywhere in the app — confirmed directly by reading every file (`requirements.txt` has no DB driver, no auth library; `.gitignore`/`.dockerignore` both exclude `.env*`/`*.pem`/`*.key` and no such files exist in the repo). | Even for a Low-risk toy repo, sharing whole files instead of only the relevant function bodies gives the AI more surface area than a task strictly needs. For a real project I would default to sharing the smallest diff or function that answers the question. |
| Read/write access to my actual Mac's task-tracker folder, via the device bridge, so this session could commit and stage a git bundle for me to push (used for both the `002b58a` mid-course fix and this `final-project` branch) | Medium | This is more than sharing source code — it is giving an AI agent the ability to read and write files on my real computer, even though it was scoped to one project folder. Nothing sensitive lives in that folder, but the *mechanism* (device access) is a bigger grant than "look at this code." | Scope the grant as narrowly as the tool allows (a single project folder, not a home directory), and always review the diff/bundle before it's applied — which is what happened here (I reviewed `git diff`/`git status` before every push), but a stricter habit would be to require that review step explicitly every time rather than trusting the agent's own "diff looks clean" claim. |
| Full `pytest -v` output, `curl` request/response bodies against my locally running backend, and Playwright screenshots of the local frontend | Low | All of this is synthetic test data and UI screenshots of a toy Kanban board with no real task content — task titles like "Claim check task" created purely to verify a status code. No personal or production data ever appears in test fixtures (confirmed by reading `tests/conftest.py`: fixtures use literal strings like `"Test Task"`, not real data). | No change needed for this project; for a real product I would never let an agent screenshot or curl a UI/API that could surface real customer records, even in a "just checking a status code" context. |
| My own name and email (`malekhomeissy@gmail.com`) as git commit author, and as the repo owner's GitHub handle | Low | Already public — every commit in this repo, including the ones from before AI was involved at all, carries this same author identity, and the repo itself is public. | None needed; this is normal authorship metadata, not something the AI could misuse differently than any other public git history. |
| Facilitator feedback text (the exact NOT MET rubric comment about the null-title bug) | Low | Course feedback about a public toy-project submission, not confidential in any way that matters here — no student records, no grades tied to an identifiable cohort, just one line of rubric text. | None needed. |
| The full set of Module 4/5 course PDFs (lecture notes, prompt libraries, project brief) | Low | Course materials, not my own private data — I'm the one choosing to reference them to complete an assignment for the same course they came from. | None needed; these aren't sensitive, they're instructional content. |

## What I Received From AI

Real AI-assisted outputs from this project, cited against the actual
commits/files that carry them — not a generic list of "things AI can do."

| Output | Where it lives | Evidence |
|---|---|---|
| Initial FastAPI app skeleton: `TaskCreate`/`TaskUpdate`/`TaskResponse` Pydantic models, in-memory `storage.py`, CRUD routes in `main.py` | Commit `1a304bd` "Complete Modules 1-3 Task Tracker baseline" | Full diff of that commit; still the structural basis of every file in `app/` today. |
| `_is_overdue` due-date business rule and its extraction into a standalone pure function | Commits `3a7adbc` (Feature 1) and `3036eab` (refactor) | `app/models.py`; prompt/response summary for both steps recorded in `docs/midcourse/prompt-log.md`, Feature 1 section. |
| `_validate_tags` tag validation helper (length caps, blank rejection, trimming) | Commit `5539031` "Feature 2: tags/labels" | `app/models.py` lines ~53-64; full prompt and the resulting off-by-one bug are recorded in `docs/midcourse/prompt-log.md`, Prompt 2.2/2.3. |
| `validate_status_transition` state-machine enforcement in `app/business_rules.py` | Commit `1a304bd` (Modules 1-3 baseline) | `app/business_rules.py`, full file; referenced directly in `AGENTS.md`'s business-rules section. |
| The original (buggy) `TaskUpdate.validate_title` that silently accepted `title: null` on PATCH | Introduced in the Modules 1-3 baseline, still present through `mid-course-project` until this session's fix | Root cause of the facilitator NOT MET; fixed in commit `002b58a`. This is a real example of an AI-authored validator that was *wrong* and shipped for multiple modules before a human (the facilitator, then me) caught it. |
| Pytest test suites for every feature (24 baseline + 9 due-date + 12 tags + 1 null-title regression = 46 tests) | `tests/test_tasks.py`, commits `1a304bd`, `3a7adbc`, `5539031`, `002b58a` | `docs/midcourse/prompt-log.md` and `docs/midcourse/verification.md` record the exact prompts used and, notably, two real test failures the AI's own first-draft code caused (the missing Done-status check in Prompt 1.2, and the tags off-by-one in Prompt 2.2), both caught by tests written from a *separate* prompt, not by re-reading the implementation. |
| `docs/midcourse/mini-adr.md` design-decision record, including a documented instance of the AI's first instinct being wrong (Decision 3: it initially leaned toward a normalized `Tag` model before catching that this violated the stated constraints) | `docs/midcourse/mini-adr.md` | Read in full this session; Decision 3 is a real, admitted overreach that had to be walked back before any code was written. |
| `AGENTS.md`, `.github/workflows/ci.yml`, `Dockerfile`, `.dockerignore`, `docs/release-evidence.md`, `docs/security-review.md` (this session's Module 5 work) | This branch, `final-project` | Every claim in these files was checked against the real repo before being written (see the "Files inspected" list at the top of `docs/security-review.md` and the verification commands in `docs/release-evidence.md`). |

## Generated Code Ownership Trace

**Code block chosen:** `_validate_tags()` in `app/models.py` (introduced in
commit `5539031`, "Feature 2: tags/labels").

```python
MAX_TAGS = 5
MAX_TAG_LENGTH = 20

def _validate_tags(value: List[str]) -> List[str]:
    if len(value) > MAX_TAGS:
        raise ValueError(f"A task may have at most {MAX_TAGS} tags")
    cleaned = []
    for tag in value:
        stripped = tag.strip()
        if not stripped:
            raise ValueError("Tags cannot be blank or whitespace-only")
        if len(stripped) > MAX_TAG_LENGTH:
            raise ValueError(f"Each tag must be {MAX_TAG_LENGTH} characters or fewer")
        cleaned.append(stripped)
    return cleaned
```

I picked this one specifically because it has a real, documented bug in its
first-draft history (see `docs/midcourse/prompt-log.md`, Prompt 2.2/2.3) —
it's a better test of whether I actually understand it than a block that
worked correctly on the first try.

1. **What it does.** It's called from a `field_validator` on both
   `TaskCreate.tags` and `TaskUpdate.tags` (via `@field_validator("tags")`
   further down in `app/models.py`). It takes the raw list of tag strings a
   client sent, rejects the whole request with a `ValueError` (which
   Pydantic turns into a 422) if there are too many tags or any tag is
   blank/too long, and otherwise returns a *cleaned* list — every tag
   trimmed of leading/trailing whitespace — which is what actually gets
   stored.

2. **Why it's needed.** Without it, a client could submit unlimited tags of
   unlimited length (unbounded growth into `storage`, the same class of
   issue flagged as AI-1 in `docs/security-review.md` for the still-unbounded
   `description`/`assignee` fields), or a tag that's just `"   "` — visually
   empty but not caught by a plain "is it missing" check. Centralizing the
   rule in one function instead of writing it separately for `TaskCreate`
   and `TaskUpdate` also means both routes enforce exactly the same rule,
   which matters because PATCH and POST go through two different Pydantic
   models.

3. **What would break if it were removed or changed carelessly.** Deleting
   it (or the `field_validator` that calls it) would silently reopen the
   unbounded-tags/blank-tag hole — no test would fail immediately at import
   time, but `test_create_task_with_six_tags_is_rejected` and
   `test_blank_tag_is_rejected` (both in `tests/test_tasks.py`) would start
   failing, which is exactly how this class of regression gets caught here.
   Changing `len(value) > MAX_TAGS` back to `len(value) >= MAX_TAGS` — the
   original AI-authored version — would silently break the boundary case
   again: exactly 5 tags would start being rejected instead of accepted,
   which is precisely the bug `test_create_task_with_exactly_five_tags_succeeds`
   exists to catch.

4. **Any framework-behavior assumption baked into it.** It assumes that
   raising `ValueError` inside a Pydantic `field_validator` is enough to
   produce a 422 response with FastAPI — there's no manual `HTTPException`
   or status-code handling in this function at all. That's correct because
   FastAPI catches Pydantic's `ValidationError` and translates it
   automatically, but it's an assumption specific to this
   FastAPI+Pydantic-v2 stack; a function like this dropped into a different
   framework would need explicit error-response handling added.

5. **Whether I fully understand it, or am flagging a gap.** I fully
   understand it — including the one part that isn't obvious from reading
   the function alone: why `>` and not `>=` is correct for the count check.
   The spec (and the tests) treat "5 tags" as the *inclusive* upper bound
   (5 is allowed, 6 is not), so the check has to fire only once the count
   *exceeds* the limit, not once it *reaches* it. That's the exact detail
   the AI's first draft got backwards, and it's the kind of one-character
   boundary mistake that's easy to miss just by reading the code — it only
   became obvious once `test_create_task_with_exactly_five_tags_succeeds`
   actually failed at `assert 422 == 201`. This is why I chose this block
   over one that worked correctly on the first try.
