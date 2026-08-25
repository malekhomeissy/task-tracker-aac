# My AI Playbook

This is drafted from the actual evidence in this repo — the prompt logs,
the ADRs, the commit history, the security review, and this session's own
context-strategy experiment (`docs/architecture.md`). A few lines are
marked **[FOR YOUR REVIEW]** where they're closer to a personal
preference than something I can back with a specific event from this
project — those are flagged rather than made up, and are worth reading
over before submission rather than treating as finished.

## When I reach for AI first

- **Scaffolding a new model/route/validator that follows an existing
  pattern already in the codebase.** Every feature in this repo (due
  dates, tags, the CI workflow, the Dockerfile) started as an AI-drafted
  first pass against an explicit spec, then got corrected — see the
  prompt-by-prompt record in `docs/midcourse/prompt-log.md`.
- **Writing the test suite for a feature, once the behavior is agreed
  on.** Both real bugs this project ever shipped (the missing Done-status
  check on `is_overdue`, the tags off-by-one) were caught by AI-written
  tests failing against AI-written code — which only worked because the
  tests were written from a separate, explicit prompt describing expected
  behavior, not copied from the implementation.
- **A first-pass architecture or security sweep of a codebase this
  size**, specifically to have something concrete to grade against — not
  to trust outright. `docs/security-review.md`'s AI Findings table is
  exactly this: a starting point that then got checked, and two of its
  eight findings turned out to be False Positive or Noise.

## When I do not reach for AI first

- **Deciding the data shape for a new feature before any code exists.**
  The tags feature's design step (`docs/midcourse/mini-adr.md`, Decision
  3) shows why: the AI's own first instinct was a normalized `Tag` table,
  which was the *wrong* answer for this project's stated constraints. I
  ask for options and tradeoffs first, and make the call myself, instead
  of accepting the first design offered.
- **Pushing anything to GitHub.** This came up literally in this
  session — the AI agent working on this repo could not push directly
  (the git proxy rejected it), so every push in this project's history
  has gone through me running `git push` myself after reading the diff.
  I'm keeping that as a deliberate rule, not just a workaround forced by
  the tooling.
- **Grading my own review work.** The Comments feature plan
  (`docs/decisions/comments-feature-plan.md`) and the security review
  both required a second, independent pass — reconciling AI output
  against my own read of the code — rather than accepting the AI's first
  answer as the finished product.

## My non-negotiables

- Never let generated code touch `main` without the diff being reviewed
  first — no exceptions, regardless of how small the change looks.
- Never accept "all tests pass" as true without actually running the
  suite and reading the number myself. Two real bugs in this repo's
  history would have shipped if I hadn't.
- Never record a security or plan-critique finding as accepted without a
  grade attached (Valid/False Positive/Noise; Right/Missing/Needs
  Resequencing) — see `docs/security-review.md` and
  `docs/decisions/comments-feature-plan.md` for what that looks like in
  practice.
- Never paste real credentials or real user data into a prompt — not
  applicable in the literal sense for this toy project (there's no real
  user data anywhere in it), but it's the rule I'm carrying forward.

## My review rules

- Re-run the actual command a document claims ran, don't just read the
  claim (`docs/release-evidence.md`'s claim-vs-reality log is built this
  way — every status-code claim was checked with a live `curl`, not
  assumed from the route decorator).
- When something genuinely can't be verified in the environment I have
  (this session's inability to run Docker), say so in the document
  instead of writing a result as if it happened.
- Treat an AI-authored ADR or design doc as a claim to check, not a
  record of fact, until I've confirmed it against the actual code —
  `docs/architecture-B.md` in this same submission is a live example of a
  plausible-sounding AI claim (that `description`/`assignee` share
  `title`/`tags`'s validation) that was wrong, caught only by reading the
  real file.

## What I am still figuring out

- Where exactly the line is between "AI drafts, I verify" and "I should
  just write this part myself" for small, fast changes — the null-title
  fix in this repo went through the full verify-and-test cycle, but I
  don't have a settled rule yet for when that full cycle is worth it
  versus overkill. **[FOR YOUR REVIEW: this is a genuine open question
  for me, not something the repo history settles one way or the other —
  worth writing in your own words if you want a real answer here.]**
- How much to trust an AI's own confidence language ("almost certainly,"
  "this pattern is consistent") — `docs/architecture-B.md` in this
  session is the clearest evidence I have that confident-sounding claims
  can still be wrong, but I don't yet have a reliable way to catch that
  *before* checking the file, only after. **[FOR YOUR REVIEW: also
  genuinely unresolved — flagging rather than pretending I have a rule
  for it.]**

## Decision Card

| Situation | My rule |
|---|---|
| New feature | Plan first without AI (or grade its plan hard, per `docs/decisions/comments-feature-plan.md`), decide the data shape myself, then let AI draft the implementation against my decision. |
| Code review | Treat every AI comment as a claim to grade (Useful/Noise/Wrong), not an accepted finding — same pattern as the Valid/False-Positive/Noise grading in `docs/security-review.md`. |
| Debugging | Run the failing test myself and read the actual assertion before asking AI to explain or fix it — both real bugs in this repo's history were found this way, not by asking AI to review its own code. |
| Infrastructure (CI/Docker/deploy) | Read the generated config line-by-line against a known anti-pattern checklist (no `continue-on-error`, no `\|\| true`, pinned versions, non-root user) before trusting it — that checklist is what actually verified `.github/workflows/ci.yml` and the `Dockerfile` in this submission. |
| Never-paste | Real credentials, tokens, or any real user/customer data — no exceptions. |
| One rule | If I can't point to the specific file or test that confirms an AI claim, I don't submit it as fact — I mark it as unverified or check it first. |
