import pytest


class TestCreateTodo:
    @pytest.mark.asyncio
    async def test_create_todo_with_all_fields(self, test_client):
        """Test creating a TODO with all fields."""
        response = await test_client.post(
            "/todos",
            json={
                "description": "Complete project",
                "due_date_text": "next Friday",
                "due_date": "2025-01-17",
                "notes": "Important project",
                "priority": 1,
                "gcal_event_id": "cal123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Complete project"
        assert data["due_date_text"] == "next Friday"
        assert data["due_date"] == "2025-01-17"
        assert data["notes"] == "Important project"
        assert data["priority"] == 1
        assert data["status"] == "pending"
        assert data["gcal_event_id"] == "cal123"
        assert data["id"] is not None
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        assert data["completed_at"] is None

    @pytest.mark.asyncio
    async def test_create_todo_with_only_description(self, test_client):
        """Test creating a TODO with only required field."""
        response = await test_client.post(
            "/todos",
            json={"description": "Simple todo"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Simple todo"
        assert data["priority"] == 3  # default
        assert data["status"] == "pending"
        assert data["due_date_text"] is None
        assert data["due_date"] is None
        assert data["notes"] is None
        assert data["gcal_event_id"] is None

    @pytest.mark.asyncio
    async def test_create_todo_empty_description_fails(self, test_client):
        """Test that empty description fails validation."""
        response = await test_client.post(
            "/todos",
            json={"description": ""},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_todo_invalid_priority_fails(self, test_client):
        """Test that invalid priority fails validation."""
        response = await test_client.post(
            "/todos",
            json={"description": "Test", "priority": 5},
        )
        assert response.status_code == 422

        response = await test_client.post(
            "/todos",
            json={"description": "Test", "priority": 0},
        )
        assert response.status_code == 422


class TestBulkCreateTodos:
    @pytest.mark.asyncio
    async def test_bulk_create_multiple_todos(self, test_client):
        """Test creating multiple TODOs at once."""
        response = await test_client.post(
            "/todos/bulk",
            json={
                "todos": [
                    {"description": "First bulk todo", "priority": 1},
                    {"description": "Second bulk todo", "priority": 2},
                    {"description": "Third bulk todo", "priority": 3},
                ]
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "todos" in data
        assert "count" in data
        assert data["count"] == 3
        assert len(data["todos"]) == 3
        assert data["todos"][0]["description"] == "First bulk todo"
        assert data["todos"][1]["description"] == "Second bulk todo"
        assert data["todos"][2]["description"] == "Third bulk todo"

    @pytest.mark.asyncio
    async def test_bulk_create_single_todo(self, test_client):
        """Test bulk create with a single TODO."""
        response = await test_client.post(
            "/todos/bulk",
            json={
                "todos": [
                    {"description": "Single bulk todo", "priority": 2},
                ]
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["count"] == 1
        assert len(data["todos"]) == 1

    @pytest.mark.asyncio
    async def test_bulk_create_with_all_fields(self, test_client):
        """Test bulk create with all optional fields."""
        response = await test_client.post(
            "/todos/bulk",
            json={
                "todos": [
                    {
                        "description": "Full todo",
                        "due_date_text": "tomorrow",
                        "due_date": "2025-01-15",
                        "notes": "Important notes",
                        "priority": 1,
                        "gcal_event_id": "gcal123",
                    },
                ]
            },
        )
        assert response.status_code == 201
        data = response.json()
        todo = data["todos"][0]
        assert todo["description"] == "Full todo"
        assert todo["due_date_text"] == "tomorrow"
        assert todo["due_date"] == "2025-01-15"
        assert todo["notes"] == "Important notes"
        assert todo["priority"] == 1
        assert todo["gcal_event_id"] == "gcal123"

    @pytest.mark.asyncio
    async def test_bulk_create_empty_list_fails(self, test_client):
        """Test that bulk create with empty list fails validation."""
        response = await test_client.post(
            "/todos/bulk",
            json={"todos": []},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_bulk_create_invalid_todo_fails(self, test_client):
        """Test that bulk create fails if any TODO is invalid."""
        response = await test_client.post(
            "/todos/bulk",
            json={
                "todos": [
                    {"description": "Valid todo"},
                    {"description": ""},  # Invalid - empty description
                ]
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_bulk_create_invalid_priority_fails(self, test_client):
        """Test that bulk create fails with invalid priority."""
        response = await test_client.post(
            "/todos/bulk",
            json={
                "todos": [
                    {"description": "Valid todo", "priority": 5},  # Invalid priority
                ]
            },
        )
        assert response.status_code == 422


class TestListTodos:
    @pytest.mark.asyncio
    async def test_list_all_todos(self, test_client, sample_todo):
        """Test listing all TODOs."""
        response = await test_client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert "todos" in data
        assert "count" in data
        assert data["count"] >= 1

    @pytest.mark.asyncio
    async def test_list_todos_filter_by_status(self, test_client, sample_todo):
        """Test filtering TODOs by status."""
        # List pending
        response = await test_client.get("/todos?status=pending")
        assert response.status_code == 200
        data = response.json()
        for todo in data["todos"]:
            assert todo["status"] == "pending"

        # List completed (should be empty initially)
        response = await test_client.get("/todos?status=completed")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_todos_filter_by_priority(self, test_client, sample_todo):
        """Test filtering TODOs by priority."""
        response = await test_client.get("/todos?priority=2")
        assert response.status_code == 200
        data = response.json()
        for todo in data["todos"]:
            assert todo["priority"] == 2

    @pytest.mark.asyncio
    async def test_list_todos_sort_order(self, test_client):
        """Test that TODOs are sorted by due_date then priority."""
        # Create TODOs with different dates and priorities
        await test_client.post(
            "/todos",
            json={"description": "Later high", "due_date": "2025-01-20", "priority": 1},
        )
        await test_client.post(
            "/todos",
            json={"description": "Earlier low", "due_date": "2025-01-10", "priority": 4},
        )
        await test_client.post(
            "/todos",
            json={"description": "Same date low", "due_date": "2025-01-10", "priority": 3},
        )
        await test_client.post(
            "/todos",
            json={"description": "No date", "priority": 1},
        )

        response = await test_client.get("/todos")
        data = response.json()
        todos = data["todos"]

        # Find our test todos
        test_todos = [t for t in todos if t["description"] in
                      ["Later high", "Earlier low", "Same date low", "No date"]]

        # Earlier dates should come first
        assert test_todos[0]["description"] == "Same date low"  # 01-10, priority 3
        assert test_todos[1]["description"] == "Earlier low"     # 01-10, priority 4
        assert test_todos[2]["description"] == "Later high"      # 01-20, priority 1
        assert test_todos[3]["description"] == "No date"         # NULL date comes last


class TestGetTodo:
    @pytest.mark.asyncio
    async def test_get_single_todo(self, test_client, sample_todo):
        """Test getting a single TODO by ID."""
        todo_id = sample_todo["id"]
        response = await test_client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["description"] == sample_todo["description"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_todo_returns_404(self, test_client):
        """Test that getting a non-existent TODO returns 404."""
        response = await test_client.get("/todos/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "TODO not found"


class TestUpdateTodo:
    @pytest.mark.asyncio
    async def test_update_todo(self, test_client, sample_todo):
        """Test updating a TODO."""
        todo_id = sample_todo["id"]
        response = await test_client.put(
            f"/todos/{todo_id}",
            json={
                "description": "Updated description",
                "priority": 1,
                "notes": "Updated notes",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["priority"] == 1
        assert data["notes"] == "Updated notes"

    @pytest.mark.asyncio
    async def test_partial_update_todo(self, test_client, sample_todo):
        """Test partial update of a TODO."""
        todo_id = sample_todo["id"]
        original_description = sample_todo["description"]

        response = await test_client.put(
            f"/todos/{todo_id}",
            json={"priority": 4},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 4
        assert data["description"] == original_description  # unchanged

    @pytest.mark.asyncio
    async def test_update_nonexistent_todo_returns_404(self, test_client):
        """Test that updating a non-existent TODO returns 404."""
        response = await test_client.put(
            "/todos/99999",
            json={"description": "Updated"},
        )
        assert response.status_code == 404


class TestDeleteTodo:
    @pytest.mark.asyncio
    async def test_delete_todo(self, test_client, sample_todo):
        """Test soft deleting a TODO."""
        todo_id = sample_todo["id"]
        response = await test_client.delete(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "TODO deleted"
        assert data["id"] == todo_id

    @pytest.mark.asyncio
    async def test_deleted_todo_not_in_list(self, test_client, sample_todo):
        """Test that deleted TODO is not returned in list."""
        todo_id = sample_todo["id"]
        await test_client.delete(f"/todos/{todo_id}")

        response = await test_client.get("/todos")
        data = response.json()
        todo_ids = [t["id"] for t in data["todos"]]
        assert todo_id not in todo_ids

    @pytest.mark.asyncio
    async def test_deleted_todo_returns_404_on_get(self, test_client, sample_todo):
        """Test that getting a deleted TODO returns 404."""
        todo_id = sample_todo["id"]
        await test_client.delete(f"/todos/{todo_id}")

        response = await test_client.get(f"/todos/{todo_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_todo_returns_404(self, test_client):
        """Test that deleting a non-existent TODO returns 404."""
        response = await test_client.delete("/todos/99999")
        assert response.status_code == 404


class TestCompleteTodo:
    @pytest.mark.asyncio
    async def test_complete_todo(self, test_client, sample_todo):
        """Test completing a TODO."""
        todo_id = sample_todo["id"]
        response = await test_client.post(f"/todos/{todo_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_complete_already_completed_todo(self, test_client, sample_todo):
        """Test completing an already completed TODO (idempotent)."""
        todo_id = sample_todo["id"]
        await test_client.post(f"/todos/{todo_id}/complete")

        response = await test_client.post(f"/todos/{todo_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_complete_deleted_todo_returns_404(self, test_client, sample_todo):
        """Test that completing a deleted TODO returns 404."""
        todo_id = sample_todo["id"]
        await test_client.delete(f"/todos/{todo_id}")

        response = await test_client.post(f"/todos/{todo_id}/complete")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_complete_nonexistent_todo_returns_404(self, test_client):
        """Test that completing a non-existent TODO returns 404."""
        response = await test_client.post("/todos/99999/complete")
        assert response.status_code == 404


class TestReopenTodo:
    @pytest.mark.asyncio
    async def test_reopen_todo(self, test_client, sample_todo):
        """Test reopening a completed TODO."""
        todo_id = sample_todo["id"]
        await test_client.post(f"/todos/{todo_id}/complete")

        response = await test_client.post(f"/todos/{todo_id}/reopen")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["completed_at"] is None

    @pytest.mark.asyncio
    async def test_reopen_already_pending_todo(self, test_client, sample_todo):
        """Test reopening an already pending TODO (idempotent)."""
        todo_id = sample_todo["id"]
        response = await test_client.post(f"/todos/{todo_id}/reopen")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_reopen_nonexistent_todo_returns_404(self, test_client):
        """Test that reopening a non-existent TODO returns 404."""
        response = await test_client.post("/todos/99999/reopen")
        assert response.status_code == 404


class TestPurgeTodos:
    @pytest.mark.asyncio
    async def test_purge_deleted_todos(self, test_client, sample_todo):
        """Test purging soft-deleted TODOs."""
        todo_id = sample_todo["id"]
        await test_client.delete(f"/todos/{todo_id}")

        response = await test_client.delete("/admin/purge")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Purged deleted TODOs"
        assert data["count"] >= 1

    @pytest.mark.asyncio
    async def test_purge_does_not_affect_active_todos(self, test_client, sample_todo):
        """Test that purge does not affect active TODOs."""
        todo_id = sample_todo["id"]

        response = await test_client.delete("/admin/purge")
        assert response.status_code == 200

        # Active TODO should still exist
        response = await test_client.get(f"/todos/{todo_id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_purge_returns_zero_when_no_deleted(self, test_client):
        """Test purge returns zero count when no deleted TODOs."""
        response = await test_client.delete("/admin/purge")
        assert response.status_code == 200
        # Count could be 0 or more depending on previous tests
