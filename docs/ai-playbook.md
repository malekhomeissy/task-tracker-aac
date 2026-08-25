# My AI Playbook

This playbook comes from the actual work in this Task Tracker: the mid-course
prompt log and Break Tests, the facilitator-reported null-title bug, the CI
and Docker checks, and the final security/review exercises.

## When I reach for AI first

- I use AI first when a task follows an existing pattern and the expected
  behavior is already clear, such as drafting validators, tests, CI, Docker,
  or documentation from a specific repo-grounded brief.
- I use AI for a first-pass review or security sweep when I want broad
  coverage, but I treat the output as a list of claims to grade rather than a
  list of facts.
- I use AI for debugging after I have the exact failing test, request, or
  error. The null-title resubmission reinforced that a specific failing case
  is much more useful than a vague "fix validation" prompt.

## When I do not reach for AI first

- I do not let AI make the final architecture or scope decision for me. The
  tags work showed that a more complex normalized design can sound reasonable
  even when the assignment explicitly asks for something simpler.
- I do not use AI output as proof that code works. I run the tests, the app,
  the documented command, or the Docker container myself.
- I do not accept an AI review comment just because it sounds professional. I
  verify the cited file and then grade the comment as useful, noise, or wrong.

## My non-negotiables

- Never paste `.env` files, API keys, credentials, tokens, real customer/user
  data, or production logs into an AI tool.
- Read the diff before accepting a change, especially for repo-wide tools.
- Run the relevant verification before recording a result as true.
- Do not hide failures with shortcuts such as `continue-on-error`, `|| true`,
  or skipped tests.
- If I cannot explain a changed line or config choice, I do not treat it as
  finished work.

## My review rules

1. Check the actual file or diff behind every important AI claim.
2. Run the smallest focused test first, then the full suite for regression.
3. For documentation, compare claims with the running app or code rather than
   trusting fluent wording.
4. For security/review output, record a grade and a reason before acting.
5. If the environment cannot verify something, mark it unverified instead of
   inventing evidence.

## What I am still figuring out

- How much AI assistance is worth using for very small fixes when writing the
  change directly may be faster than running a full agent workflow.
- How much context to provide up front. The architecture A/B/C exercise showed
  that more context can improve completeness but can also make answers longer
  and more confident; targeted context can be more honest for correctness-
  sensitive work.

## Decision Card

| Situation | My decision |
|---|---|
| New feature | Define the behavior and scope first, then use repo-grounded AI to draft small steps. |
| Code review | Use AI for broad first-pass coverage, then verify and grade every substantive comment myself. |
| Debugging | Start from the exact failing test/error and use AI to reason from that evidence. |
| Infrastructure | Use a terminal agent for CI/Docker drafts, but inspect config line-by-line and run the real commands before accepting it. |
| Never paste | `.env` files, API keys, credentials, tokens, real customer/user data, or production logs. |
| One rule | If I cannot point to the file, test, command, or runtime evidence behind an AI claim, I do not submit it as fact. |

I will re-read this playbook in 30 days and check whether I am still following
these rules.
