"""Module 2 model verification script (Prompt A / Verification A).

Independently checks eight behaviors of app/models.py without pytest, so it
can be run directly with: python -m tests.verify_a

Every check should print PASS. Any FAIL indicates the model layer does not
match the Module 2 spec and must be fixed before moving on.
"""

import sys

from pydantic import ValidationError

from app.models import TaskCreate, TaskPriority, TaskStatus, TaskUpdate

results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))


def run_checks() -> None:
    # 1. Whitespace-only title rejected
    try:
        TaskCreate(title="   ")
        check("1. whitespace-only title rejected", False, "no error raised")
    except ValidationError:
        check("1. whitespace-only title rejected", True)

    # 2. Empty title rejected
    try:
        TaskCreate(title="")
        check("2. empty title rejected", False, "no error raised")
    except ValidationError:
        check("2. empty title rejected", True)

    # 3. Title over 200 characters rejected
    try:
        TaskCreate(title="x" * 201)
        check("3. title over 200 characters rejected", False, "no error raised")
    except ValidationError:
        check("3. title over 200 characters rejected", True)

    # 4. Defaults: status ToDo, priority Medium, description ""
    task = TaskCreate(title="Valid title")
    defaults_ok = (
        task.status == TaskStatus.TODO
        and task.priority == TaskPriority.MEDIUM
        and task.description == ""
    )
    check(
        "4. defaults are status=ToDo, priority=Medium, description=''",
        defaults_ok,
        f"got status={task.status}, priority={task.priority}, description={task.description!r}",
    )

    # 5. Extra field rejected in TaskCreate
    try:
        TaskCreate(title="Valid title", extra_field="nope")  # type: ignore[call-arg]
        check("5. extra field rejected in TaskCreate", False, "no error raised")
    except ValidationError:
        check("5. extra field rejected in TaskCreate", True)

    # 6. id rejected in TaskCreate
    try:
        TaskCreate(title="Valid title", id="should-not-be-allowed")  # type: ignore[call-arg]
        check("6. id rejected in TaskCreate", False, "no error raised")
    except ValidationError:
        check("6. id rejected in TaskCreate", True)

    # 7. created_at rejected in TaskUpdate
    try:
        TaskUpdate(created_at="2024-01-01T00:00:00Z")  # type: ignore[call-arg]
        check("7. created_at rejected in TaskUpdate", False, "no error raised")
    except ValidationError:
        check("7. created_at rejected in TaskUpdate", True)

    # 8. Invalid status rejected
    try:
        TaskCreate(title="Valid title", status="Archived")  # type: ignore[arg-type]
        check("8. invalid status rejected", False, "no error raised")
    except ValidationError:
        check("8. invalid status rejected", True)


def main() -> int:
    run_checks()
    all_passed = True
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        line = f"{status}: {name}"
        if not passed and detail:
            line += f" ({detail})"
        print(line)
        if not passed:
            all_passed = False
    print()
    print("ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
