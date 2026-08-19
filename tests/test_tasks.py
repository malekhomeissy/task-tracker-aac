"""API tests for the Task Tracker backend (Module 2 Part 2.4).

Uses FastAPI's synchronous TestClient against the real in-memory storage
(no mocking). Storage is reset before and after every test via the
autouse `_reset_storage` fixture in conftest.py.
"""


# ---------------------------------------------------------------------------
# POST /tasks
# ---------------------------------------------------------------------------


def test_create_task_valid_returns_201_with_full_body(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Write tests",
            "description": "Cover the API",
            "status": "InProgress",
            "priority": "High",
            "assignee": "Malek",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write tests"
    assert body["description"] == "Cover the API"
    assert body["status"] == "InProgress"
    assert body["priority"] == "High"
    assert body["assignee"] == "Malek"
    assert body["id"]
    assert body["created_at"] == body["updated_at"]


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={})
    assert response.status_code == 422


def test_create_task_blank_title_returns_422(client):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_title_over_200_chars_returns_422(client):
    response = client.post("/tasks", json={"title": "x" * 201})
    assert response.status_code == 422


def test_create_task_invalid_status_returns_422(client):
    response = client.post("/tasks", json={"title": "Valid title", "status": "Archived"})
    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Valid title", "priority": "Urgent"})
    assert response.status_code == 422


def test_create_task_unknown_field_returns_422(client):
    response = client.post("/tasks", json={"title": "Valid title", "not_a_real_field": True})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------


def test_list_tasks_empty_returns_200_and_empty_list(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_created_tasks(client):
    client.post("/tasks", json={"title": "Task A"})
    client.post("/tasks", json={"title": "Task B"})
    response = client.get("/tasks")
    assert response.status_code == 200
    titles = {task["title"] for task in response.json()}
    assert titles == {"Task A", "Task B"}


def test_list_tasks_filter_by_status_returns_only_matches(client):
    client.post("/tasks", json={"title": "Still todo"})
    in_progress = client.post("/tasks", json={"title": "Started", "status": "InProgress"}).json()

    response = client.get("/tasks", params={"status": "InProgress"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == in_progress["id"]


def test_list_tasks_filter_by_priority_returns_only_matches(client):
    client.post("/tasks", json={"title": "Low one", "priority": "Low"})
    high = client.post("/tasks", json={"title": "High one", "priority": "High"}).json()

    response = client.get("/tasks", params={"priority": "High"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == high["id"]


def test_list_tasks_combined_status_and_priority_filter(client):
    target = client.post(
        "/tasks", json={"title": "Match", "status": "ToDo", "priority": "High"}
    ).json()
    client.post("/tasks", json={"title": "Wrong status", "status": "InProgress", "priority": "High"})
    client.post("/tasks", json={"title": "Wrong priority", "status": "ToDo", "priority": "Low"})

    response = client.get("/tasks", params={"status": "ToDo", "priority": "High"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == target["id"]


def test_list_tasks_filter_no_match_returns_200_and_empty_list(client):
    client.post("/tasks", json={"title": "Only todo task"})
    response = client.get("/tasks", params={"status": "Done"})
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /tasks/{task_id}
# ---------------------------------------------------------------------------


def test_get_task_by_id_returns_task(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created_task["id"]


def test_get_task_by_id_not_found_returns_404_with_detail(client):
    response = client.get("/tasks/does-not-exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# PATCH /tasks/{task_id}
# ---------------------------------------------------------------------------


def test_patch_partial_update_keeps_other_fields(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"description": "Updated desc"})
    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Updated desc"
    assert body["title"] == created_task["title"]
    assert body["priority"] == created_task["priority"]


def test_patch_not_found_returns_404(client):
    response = client.patch("/tasks/does-not-exist", json={"title": "New title"})
    assert response.status_code == 404


def test_patch_invalid_title_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"title": "   "})
    assert response.status_code == 422


def test_patch_valid_transition_todo_to_inprogress_returns_200(client, created_task):
    assert created_task["status"] == "ToDo"
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "InProgress"})
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_patch_invalid_transition_todo_to_done_returns_422(client, created_task):
    assert created_task["status"] == "ToDo"
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "Done"})
    assert response.status_code == 422
    assert "transition" in response.json()["detail"].lower()


def test_patch_same_status_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "ToDo"})
    assert response.status_code == 422


def test_patch_unrelated_update_does_not_trigger_transition_validation(client, created_task):
    # created_task is ToDo; a title-only PATCH must succeed even though ToDo has
    # only one valid outgoing transition and no status is being changed here.
    response = client.patch(f"/tasks/{created_task['id']}", json={"title": "Renamed only"})
    assert response.status_code == 200
    assert response.json()["status"] == "ToDo"
    assert response.json()["title"] == "Renamed only"


# ---------------------------------------------------------------------------
# DELETE /tasks/{task_id}
# ---------------------------------------------------------------------------


def test_delete_existing_returns_204_no_body(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client):
    response = client.delete("/tasks/does-not-exist")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Mid-course Feature 1: Due Dates + Overdue Filter
# ---------------------------------------------------------------------------


def test_create_task_with_valid_due_date(client):
    response = client.post("/tasks", json={"title": "Ship report", "due_date": "2099-01-15"})
    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == "2099-01-15"
    assert body["is_overdue"] is False


def test_create_task_invalid_due_date_returns_422(client):
    response = client.post("/tasks", json={"title": "Bad date", "due_date": "not-a-date"})
    assert response.status_code == 422


def test_patch_update_due_date(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"due_date": "2099-06-01"})
    assert response.status_code == 200
    assert response.json()["due_date"] == "2099-06-01"


def test_patch_clear_due_date(client, created_task):
    client.patch(f"/tasks/{created_task['id']}", json={"due_date": "2099-06-01"})
    response = client.patch(f"/tasks/{created_task['id']}", json={"due_date": None})
    assert response.status_code == 200
    assert response.json()["due_date"] is None


def test_overdue_detection_true_for_past_incomplete_task(client):
    created = client.post("/tasks", json={"title": "Late task", "due_date": "2000-01-01"}).json()
    assert created["status"] == "ToDo"
    assert created["is_overdue"] is True


def test_future_due_date_is_not_overdue(client):
    created = client.post("/tasks", json={"title": "Future task", "due_date": "2099-01-01"}).json()
    assert created["is_overdue"] is False


def test_completed_past_due_task_is_not_overdue(client):
    created = client.post("/tasks", json={"title": "Late but done", "due_date": "2000-01-01"}).json()
    # Route it through the only legal path to Done: ToDo -> InProgress -> Done.
    client.patch(f"/tasks/{created['id']}", json={"status": "InProgress"})
    done = client.patch(f"/tasks/{created['id']}", json={"status": "Done"}).json()
    assert done["status"] == "Done"
    assert done["is_overdue"] is False


def test_overdue_filter_returns_only_overdue_tasks(client):
    overdue_task = client.post("/tasks", json={"title": "Overdue", "due_date": "2000-01-01"}).json()
    client.post("/tasks", json={"title": "Not overdue", "due_date": "2099-01-01"})
    client.post("/tasks", json={"title": "No due date"})

    response = client.get("/tasks", params={"overdue": "true"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == overdue_task["id"]


def test_overdue_filter_no_match_returns_200_and_empty_list(client):
    client.post("/tasks", json={"title": "Not overdue", "due_date": "2099-01-01"})
    response = client.get("/tasks", params={"overdue": "true"})
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Mid-course Feature 2: Tags/Labels
# ---------------------------------------------------------------------------


def test_create_task_default_tags_is_empty_list(client):
    response = client.post("/tasks", json={"title": "No tags given"})
    assert response.status_code == 201
    assert response.json()["tags"] == []


def test_create_task_with_valid_tags(client):
    response = client.post("/tasks", json={"title": "Tagged", "tags": ["backend", "urgent"]})
    assert response.status_code == 201
    assert response.json()["tags"] == ["backend", "urgent"]


def test_create_task_trims_whitespace_in_tags(client):
    response = client.post("/tasks", json={"title": "Trim me", "tags": ["  backend  ", "ui"]})
    assert response.status_code == 201
    assert response.json()["tags"] == ["backend", "ui"]


def test_create_task_blank_tag_returns_422(client):
    response = client.post("/tasks", json={"title": "Bad tag", "tags": ["ok", "   "]})
    assert response.status_code == 422


def test_create_task_with_exactly_five_tags_succeeds(client):
    tags = ["a", "b", "c", "d", "e"]
    response = client.post("/tasks", json={"title": "Five tags", "tags": tags})
    assert response.status_code == 201
    assert response.json()["tags"] == tags


def test_create_task_with_six_tags_returns_422(client):
    tags = ["a", "b", "c", "d", "e", "f"]
    response = client.post("/tasks", json={"title": "Six tags", "tags": tags})
    assert response.status_code == 422


def test_create_task_tag_over_20_chars_returns_422(client):
    response = client.post("/tasks", json={"title": "Long tag", "tags": ["x" * 21]})
    assert response.status_code == 422


def test_create_task_tag_exactly_20_chars_succeeds(client):
    tag = "x" * 20
    response = client.post("/tasks", json={"title": "Exact tag", "tags": [tag]})
    assert response.status_code == 201
    assert response.json()["tags"] == [tag]


def test_patch_update_tags(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"tags": ["new-tag"]})
    assert response.status_code == 200
    assert response.json()["tags"] == ["new-tag"]


def test_patch_unrelated_update_preserves_tags(client):
    created = client.post("/tasks", json={"title": "Keep my tags", "tags": ["keep-me"]}).json()
    response = client.patch(f"/tasks/{created['id']}", json={"description": "Updated desc only"})
    assert response.status_code == 200
    assert response.json()["tags"] == ["keep-me"]
    assert response.json()["description"] == "Updated desc only"


def test_tag_filter_returns_only_matching_tasks(client):
    match = client.post("/tasks", json={"title": "Has tag", "tags": ["release"]}).json()
    client.post("/tasks", json={"title": "No match", "tags": ["backend"]})
    client.post("/tasks", json={"title": "No tags at all"})

    response = client.get("/tasks", params={"tag": "release"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == match["id"]


def test_tag_filter_no_match_returns_200_and_empty_list(client):
    client.post("/tasks", json={"title": "Has tag", "tags": ["release"]})
    response = client.get("/tasks", params={"tag": "nonexistent"})
    assert response.status_code == 200
    assert response.json() == []
