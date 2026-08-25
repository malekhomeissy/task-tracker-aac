# AI Usage Rules — Task Tracker Project

These are the actual rules I followed (and, in a couple of places, learned
the hard way I should have followed) while building this project across
Modules 1-5. They're specific to what actually happened in this repo, not
a generic AI-safety policy.

## Never paste

- **Never paste real credentials, tokens, or `.env` contents into a prompt
  or into code an AI writes.** This project never needed any — there's no
  database, no auth library, no API keys anywhere in `requirements.txt` —
  but the rule stands for anything I build after this course, where that
  won't be true.
- **Never paste real user data into a test or a prompt**, even to "just
  check formatting." Every test fixture in `tests/conftest.py` uses
  obviously fake data (`"Test Task"`, `"Feature task"`) instead of anything
  that looks like a real record, on purpose.
- **Never let an AI agent push to `main` or force-push any branch without
  me reading the diff first.** This came up literally: when this session
  tried to push directly to GitHub, the git proxy rejected it because this
  specific repo wasn't in its authorized set — which meant the only way
  code reached GitHub was through me running `git push` myself, after
  reviewing what was being pushed. I'm keeping that as a rule going
  forward even on projects where an AI *could* push directly.

## Always verify

- **Never trust an AI's claim that "all tests pass" — run the suite
  myself and read the actual output.** Two real bugs in this repo's
  history were only caught this way, not by re-reading the code: the
  Prompt-1.2 `is_overdue` implementation that forgot to exclude Done tasks,
  and the Prompt-2.2 tags validator that used `>=` instead of `>` on the
  5-tag boundary. Both are documented with the actual failing assertion in
  `docs/midcourse/prompt-log.md`. If I had just read the code and believed
  it looked right, both bugs would have shipped.
- **Never accept a security or code-review finding at face value — grade
  it.** `docs/security-review.md` grades every AI-generated finding as
  Valid, False Positive, or Noise, with a stated reason for each grade.
  Two of the eight AI findings in that document are False Positive or
  Noise on purpose, because an AI security scan of this size of codebase
  reliably produces at least a couple of findings that sound serious but
  don't hold up against what the code actually does (a SQL-injection claim
  against a codebase with no SQL anywhere in it, for one).
  Grading instead of accepting is the whole point of that exercise.
- **Re-run the exact command a doc claims, don't just read the doc.**
  Every status-code claim in `docs/release-evidence.md`'s "Documentation
  claim-vs-reality log" was checked with a real `curl` against the running
  backend before being written down as confirmed, not assumed correct
  because it matched what the route decorator said.
- **When an AI agent can't actually run something (this session's
  Docker daemon, for example), say so instead of writing a result as if it
  ran.** `docs/release-evidence.md`'s "Environment limitation" section is
  there because I would rather have an honest gap than a fabricated Docker
  build log.

## How AI contributions get recorded

- **Every AI-assisted feature gets a real prompt log, not a vague "AI
  helped with this" note.** `docs/midcourse/prompt-log.md` records the
  actual prompt text, a summary of what the AI produced, and — critically
  — whether it was accepted as-is or corrected after a real failure. A
  prompt log that only records the successes isn't an honest record.
- **Design decisions get an ADR entry, including the ones where the AI's
  first instinct was wrong.** `docs/midcourse/mini-adr.md`, Decision 3,
  records that the AI's first answer to "how should tags be modeled"
  leaned toward a normalized `Tag` table before catching that this
  violated the stated constraints — that correction is part of the record,
  not edited out.
- **Commit messages describe what changed and why, in my own words, not
  as an AI-generated changelog.** Every commit in this repo's history
  (`1a304bd` through `002b58a`) is a short, specific, human-written
  summary of the actual change — not a raw dump of what a tool did.
- **AI-authored files that carry real claims (test counts, CI behavior,
  Docker behavior) get checked against the actual repo before being
  trusted**, per the "Always verify" rules above, and the checking itself
  is written down (`docs/release-evidence.md`) so a reader doesn't have to
  take my word for it either.
