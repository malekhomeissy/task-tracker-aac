# Mid-Course Project — Reflection

For this project I used Claude (through this coding session) as basically my
whole pair-programming partner — writing the actual model/route/storage
code, drafting the pytest tests, running the test suite and reading the
output, driving the Playwright browser checks, and helping me think through
the two ADR-style decisions (whether overdue should be stored or computed,
and whether tags needed their own database table). I didn't hand-write any
of the Python or JS myself; my role was closer to reviewer and decision-maker
— I set the constraints up front (no separate Tag model, derived overdue,
specific validation rules), and then actually checked what came back against
those constraints instead of just accepting it.

The clearest moment AI helped was speed on the boring-but-necessary parts —
wiring a new field through three Pydantic models and a storage filter is
mechanical, and having it done in one pass instead of me hand-editing four
files was a real time save, especially since the existing `exclude_unset`
pattern for PATCH already worked and didn't need touching.

The clearest moment it slowed things down, honestly, was the tag-modeling
question. My first instinct when I asked "how should tags be represented"
was to reach for a proper normalized `Tag` model with its own table, which
is the "textbook" answer and is what a real production app might actually
want eventually. But this project explicitly doesn't need that, and if I'd
just gone with the first answer I would've built a bunch of unnecessary
join logic for a feature that's really just five short strings on a task.
Catching that and rejecting it before writing any code was a case where
slowing down to actually read my own constraints back mattered.

The place human review changed the actual result the most was the two real
test failures — the overdue check that ignored task status, and the
off-by-one on the 5-tag limit. Both were logic mistakes that looked
reasonable in the code but were wrong, and both only got caught because I'd
insisted on writing the edge-case tests first and actually running them
instead of eyeballing the diff and moving on.

What I took away from this is that the tests aren't a formality after the
fact — they're the thing that actually caught the two real bugs in this
project, not code review. I trust "looks right" a lot less now than I did
going in.
