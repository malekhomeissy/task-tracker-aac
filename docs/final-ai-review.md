# Final AI Review and Ownership Evidence

## AGENTS.md guardrails

- Repo-specific stack and commands included: yes — `AGENTS.md`'s "Actual
  tech stack" and "Install / run / test commands" sections are drawn
  directly from `requirements.txt` and `README.md`, not invented (e.g. it
  explicitly notes "No ORM, no database driver, no auth library, no
  frontend framework/build tool are present," which is true of this
  repo and not a generic boilerplate claim).
- Docs-first/read-first guardrail included: yes — `AGENTS.md`'s "Module 5
  / final-project boundaries" section states a read-only default posture
  with edits confined to `docs/`, and names the specific files this pass
  is allowed to touch.
- Unexpected app/frontend edits rule included: yes — the same section
  states no `app/`/`frontend/` edits except a small, justified fix
  explained in this document, and no new product features (naming
  comments specifically, pointing at `docs/decisions/comments-feature-plan.md`).

## AI code review mini-log

Reviewed one real diff: commit `002b58a`, "Fix null title validation for
task updates" (the facilitator-resubmission fix — full diff and
before/after evidence in `docs/midcourse/verification.md`).

| AI comment | Grade: Useful / Noise / Wrong | Reason | Verification or decision |
|---|---|---|---|
| "The added comment above `validate_title` documenting *why* Pydantic v2 skips validators for omitted fields is worth keeping — it's the exact non-obvious mechanism that caused the original bug, and without it a future editor could easily reintroduce the same `if value is None: return value` mistake." | Useful | This is real, specific, and tied to an actual root cause, not a generic "add comments" suggestion. | Kept as-is; verified by re-reading the comment against the root-cause explanation in `docs/midcourse/verification.md` and confirming they describe the same mechanism. |
| "This fix protects `title`. Check whether the same `Optional[str] = None`-with-no-explicit-null-guard pattern exists on any other `TaskUpdate` field, since an identical bug could exist elsewhere and just not have been reported yet." | Useful | Concrete, checkable, and it was checked — see the result below. | Verified live against a running instance of the app: `description` has the exact same gap (`PATCH {"description": null}` → `200 OK`, persists `null` into a field typed `str` on `TaskResponse`). `assignee` does not have this gap (it's genuinely `Optional[str]`, so an explicit null is correct there). Recorded as finding **M-6** in `docs/security-review.md`, not fixed — see "One AI output I rejected or corrected" below for why it wasn't fixed in this pass. |
| "Consider replacing the field-level `@field_validator("title")` with a class-level `@model_validator(mode="after")` for consistency, since a model-level validator can see all fields at once." | Wrong | There's nothing in this fix that needs to see more than one field at a time — `title`'s validity doesn't depend on any other field's value. Switching to a model-level validator would be a strictly more complex tool for the same single-field check, with no behavior difference and no test that would ever exercise the extra capability. | Rejected. The existing field-level validator, matching the pattern already used for `tags` in the same file, is the right level of complexity for what this actually checks. |
| "The commit message is unusually long for a one-function fix; a shorter message would be cleaner." | Noise | This is a style opinion with no functional consequence, and it works against this project's own established practice — every commit in this repo's history (`1a304bd` through `002b58a`) uses a detailed message describing what changed and why, which is exactly what let this review reconstruct the root cause without re-deriving it from the diff alone. | Rejected as a style preference that doesn't fit this project's actual conventions. |

## AI security mini-review

Reusing and citing `docs/security-review.md` (the full Part 5.2 read-only
audit: 8 AI findings, 6 manual findings, reconciliation, and a Top-3
backlog). Three representative findings, one from each grade:

| Finding | File evidence | Grade: Valid / False Positive / Noise | Reason | Next action |
|---|---|---|---|---|
| AI-1: `description`/`assignee` have no length cap, unlike `title`/`tags` | `app/models.py`: no `field_validator` or `Field(max_length=...)` on either field | Valid | Both fields genuinely lack a length guard that sibling fields have; the in-memory store has no size limit to compensate. | Add `Field(max_length=...)` to both, following the existing `_validate_title`/`_validate_tags` pattern. Not implemented in this pass — documented only. |
| AI-4: "SQL injection risk in task queries" | (claimed, not repo-specific) | False Positive | This repo has no SQL anywhere — `app/storage.py` is a plain Python dict, and `requirements.txt` has no database driver. Included deliberately as an example of a plausible-sounding but repo-inaccurate AI claim. | None — the finding does not apply to this codebase. |
| AI-5: "Validate all input more thoroughly" | (claimed, not repo-specific) | Noise | True of almost any API but not actionable — this project already has specific, testable validation rules for `title`, `tags`, `status`, `priority`, and `due_date`. Adds nothing beyond AI-1's specific, actionable version of the same concern. | None — superseded by AI-1. |

Full table of all 8 AI findings, 6 manual findings, and the reconciliation
between them is in `docs/security-review.md`.

## Manual security check

M-6 in `docs/security-review.md` (added during this final-project pass,
not carried over from the mid-course security review) is the manual check
for this document: while reviewing the null-title fix diff for the code
review mini-log above, I checked by hand whether the same explicit-null
gap the facilitator caught for `title` also exists on any other
`TaskUpdate` field, rather than assuming the fix was complete because it
passed its own test. I confirmed live against a running instance of the
app (not just by reading the code) that `description` has the identical
gap — `PATCH {"description": null}` returns `200 OK` and persists `null`
into a field `TaskResponse` types as a plain `str` — while `assignee`,
which is genuinely `Optional[str]`, does not have this problem. This
finding did not come from re-running or re-reading the AI security
review; it came from asking "does this fix generalize?" about a specific
already-fixed bug and testing that question directly.

## One AI output I rejected or corrected

During the code-review pass above, the AI-generated comment noted that
`description` has the same unguarded-explicit-null pattern that caused
the original facilitator-reported bug, and the natural next suggestion
would have been to apply the identical one-line fix used for `title`. I
did **not** apply that fix in this pass. This project's Module 5/final-
project ground rules are explicit that `app/` should only be touched for
a small, justified, already-explained fix, and while this fix would be
genuinely small and would follow an established pattern exactly, I chose
to record it as a documented finding (`docs/security-review.md`, M-6)
for deliberate review rather than silently expanding this submission's
scope beyond what the facilitator actually reported and what this final
project was scoped to do. This is a case of downgrading an AI-suggested
fix to a documented-but-not-applied finding, on purpose, not because the
suggestion was wrong — it's because applying it without a separate,
explicit decision to do so would have been exactly the kind of
unreviewed scope creep this course's guardrails are meant to prevent.

## Three AI usage rules

1. **Never paste:** real credentials, `.env` values, tokens, production
   logs, or real personal/customer data into AI tools or this repo. Not
   applicable in the literal sense for this course project — there is no
   real user data anywhere in it — but it's the standing rule regardless.
2. **Always verify:** never trust a claim that tests pass, that a fix is
   complete, or that a security finding is real without checking it
   directly — against the actual test output, the actual running app, or
   the actual file. Two real bugs in this repo's history (the missing
   Done-status check on `is_overdue`, the tags off-by-one) were only
   caught this way, and M-6 above exists because a fix's *completeness*
   was checked rather than assumed.
3. **Record AI contributions by:** a real prompt log with what was
   accepted vs. corrected (`docs/midcourse/prompt-log.md`), an ADR when a
   design decision was involved, including the times the AI's first
   instinct was wrong (`docs/midcourse/mini-adr.md`, Decision 3), and a
   graded finding/comment table wherever AI output is being evaluated
   rather than just narrated (`docs/security-review.md`, this document).

## Ownership statement

I can explain every change on `final-project` because I either wrote it
against a repo-grounded spec I gave explicit instructions for, or I
checked it myself against the real running app, the real test suite, or
the real file contents before recording it as true. The one place I found
AI-suggested work I chose not to apply (the `description` null-guard fix,
above), I said so directly instead of quietly including or quietly
dropping it. The security review, the governance worksheet, and the
architecture-strategy comparison all include findings and mistakes I
didn't accept at face value — including AI outputs I deliberately graded
as wrong or overconfident — because the point of this project was
demonstrating that judgment, not producing documents that look thorough.
Nothing in this submission asserts a test result, command output, or security
finding that was not actually run or checked during the project. I'm
comfortable submitting this repo as my own work because the record of what
AI drafted versus what I verified, corrected, or rejected is itself part of
the submission, not something I'm asserting after the fact.
