"""Pydantic v2 data models for the Task Tracker API.

Module 2 baseline: strict request/response models built on Pydantic v2.
Server-managed fields (id, created_at, updated_at) are never accepted from
client input; they are generated and owned by app/storage.py.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

MAX_TITLE_LENGTH = 200


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Title is required and cannot be blank")
    if len(stripped) > MAX_TITLE_LENGTH:
        raise ValueError(f"Title must be {MAX_TITLE_LENGTH} characters or fewer")
    return stripped


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_title(value)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_title(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def is_overdue(self) -> bool:
        """Derived, not stored: recomputed from due_date/status on every read.

        A task is overdue only if it has a due date in the past AND is not
        already Done. Completed tasks are never overdue, regardless of their
        due date.
        """
        if self.due_date is None:
            return False
        if self.status == TaskStatus.DONE:
            return False
        return self.due_date < date.today()
