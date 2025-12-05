import os
import tempfile

import aiosqlite
import pytest
import pytest_asyncio

from app.database import init_db
from app.models.todo import TodoCreate, TodoUpdate
from app.services import todo_service


@pytest_asyncio.fixture
async def service_db():
    """Create a fresh temporary database for service tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    await init_db(db_path)

    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
        try:
            os.unlink(db_path)
        except OSError:
            pass


class TestCreateTodo:
    @pytest.mark.asyncio
    async def test_create_todo_returns_todo_response(self, service_db):
        """Test that create_todo returns a TodoResponse."""
        data = TodoCreate(description="Test todo")
        result = await todo_service.create_todo(service_db, data)

        assert result.id is not None
        assert result.description == "Test todo"
        assert result.priority == 3
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_create_todo_with_all_fields(self, service_db):
        """Test creating a todo with all fields."""
        from datetime import date

        data = TodoCreate(
            description="Full todo",
            due_date_text="tomorrow",
            due_date=date(2025, 1, 15),
            notes="Some notes",
            priority=1,
            gcal_event_id="cal123",
        )
        result = await todo_service.create_todo(service_db, data)

        assert result.description == "Full todo"
        assert result.due_date_text == "tomorrow"
        assert result.due_date == date(2025, 1, 15)
        assert result.notes == "Some notes"
        assert result.priority == 1
        assert result.gcal_event_id == "cal123"


class TestGetTodo:
    @pytest.mark.asyncio
    async def test_get_existing_todo(self, service_db):
        """Test getting an existing todo."""
        data = TodoCreate(description="Test todo")
        created = await todo_service.create_todo(service_db, data)

        result = await todo_service.get_todo(service_db, created.id)
        assert result is not None
        assert result.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_todo_returns_none(self, service_db):
        """Test that getting a non-existent todo returns None."""
        result = await todo_service.get_todo(service_db, 99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_deleted_todo_returns_none(self, service_db):
        """Test that getting a deleted todo returns None."""
        data = TodoCreate(description="Test todo")
        created = await todo_service.create_todo(service_db, data)
        await todo_service.delete_todo(service_db, created.id)

        result = await todo_service.get_todo(service_db, created.id)
        assert result is None


class TestListTodos:
    @pytest.mark.asyncio
    async def test_list_todos_empty(self, service_db):
        """Test listing todos when empty."""
        result = await todo_service.list_todos(service_db)
        assert result == []

    @pytest.mark.asyncio
    async def test_list_todos_excludes_deleted(self, service_db):
        """Test that list excludes deleted todos."""
        data = TodoCreate(description="Test todo")
        created = await todo_service.create_todo(service_db, data)
        await todo_service.delete_todo(service_db, created.id)

        result = await todo_service.list_todos(service_db)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_todos_filter_by_status(self, service_db):
        """Test filtering by status."""
        await todo_service.create_todo(service_db, TodoCreate(description="Pending"))
        completed_data = TodoCreate(description="Completed")
        completed = await todo_service.create_todo(service_db, completed_data)
        await todo_service.complete_todo(service_db, completed.id)

        pending_result = await todo_service.list_todos(service_db, status="pending")
        assert len(pending_result) == 1
        assert pending_result[0].description == "Pending"

        completed_result = await todo_service.list_todos(service_db, status="completed")
        assert len(completed_result) == 1
        assert completed_result[0].description == "Completed"

    @pytest.mark.asyncio
    async def test_list_todos_filter_by_priority(self, service_db):
        """Test filtering by priority."""
        await todo_service.create_todo(
            service_db, TodoCreate(description="High", priority=1)
        )
        await todo_service.create_todo(
            service_db, TodoCreate(description="Low", priority=4)
        )

        result = await todo_service.list_todos(service_db, priority=1)
        assert len(result) == 1
        assert result[0].priority == 1


class TestUpdateTodo:
    @pytest.mark.asyncio
    async def test_update_todo(self, service_db):
        """Test updating a todo."""
        data = TodoCreate(description="Original")
        created = await todo_service.create_todo(service_db, data)

        update_data = TodoUpdate(description="Updated")
        result = await todo_service.update_todo(service_db, created.id, update_data)

        assert result is not None
        assert result.description == "Updated"

    @pytest.mark.asyncio
    async def test_update_nonexistent_todo_returns_none(self, service_db):
        """Test that updating non-existent todo returns None."""
        update_data = TodoUpdate(description="Updated")
        result = await todo_service.update_todo(service_db, 99999, update_data)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_with_no_changes(self, service_db):
        """Test updating with empty data."""
        data = TodoCreate(description="Original")
        created = await todo_service.create_todo(service_db, data)

        update_data = TodoUpdate()
        result = await todo_service.update_todo(service_db, created.id, update_data)

        assert result is not None
        assert result.description == "Original"

    @pytest.mark.asyncio
    async def test_update_due_date(self, service_db):
        """Test updating due_date."""
        from datetime import date

        data = TodoCreate(description="Test")
        created = await todo_service.create_todo(service_db, data)

        update_data = TodoUpdate(due_date=date(2025, 12, 31))
        result = await todo_service.update_todo(service_db, created.id, update_data)

        assert result is not None
        assert result.due_date == date(2025, 12, 31)


class TestDeleteTodo:
    @pytest.mark.asyncio
    async def test_delete_todo(self, service_db):
        """Test soft deleting a todo."""
        data = TodoCreate(description="Test")
        created = await todo_service.create_todo(service_db, data)

        result = await todo_service.delete_todo(service_db, created.id)
        assert result is True

        # Should not be retrievable
        get_result = await todo_service.get_todo(service_db, created.id)
        assert get_result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_todo_returns_false(self, service_db):
        """Test that deleting non-existent todo returns False."""
        result = await todo_service.delete_todo(service_db, 99999)
        assert result is False


class TestCompleteTodo:
    @pytest.mark.asyncio
    async def test_complete_todo(self, service_db):
        """Test completing a todo."""
        data = TodoCreate(description="Test")
        created = await todo_service.create_todo(service_db, data)

        result = await todo_service.complete_todo(service_db, created.id)

        assert result is not None
        assert result.status == "completed"
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_nonexistent_todo_returns_none(self, service_db):
        """Test that completing non-existent todo returns None."""
        result = await todo_service.complete_todo(service_db, 99999)
        assert result is None


class TestReopenTodo:
    @pytest.mark.asyncio
    async def test_reopen_todo(self, service_db):
        """Test reopening a completed todo."""
        data = TodoCreate(description="Test")
        created = await todo_service.create_todo(service_db, data)
        await todo_service.complete_todo(service_db, created.id)

        result = await todo_service.reopen_todo(service_db, created.id)

        assert result is not None
        assert result.status == "pending"
        assert result.completed_at is None

    @pytest.mark.asyncio
    async def test_reopen_nonexistent_todo_returns_none(self, service_db):
        """Test that reopening non-existent todo returns None."""
        result = await todo_service.reopen_todo(service_db, 99999)
        assert result is None


class TestPurgeDeleted:
    @pytest.mark.asyncio
    async def test_purge_deleted(self, service_db):
        """Test purging deleted todos."""
        data = TodoCreate(description="Test")
        created = await todo_service.create_todo(service_db, data)
        await todo_service.delete_todo(service_db, created.id)

        count = await todo_service.purge_deleted(service_db)
        assert count == 1

    @pytest.mark.asyncio
    async def test_purge_with_no_deleted_returns_zero(self, service_db):
        """Test purging when no deleted todos."""
        count = await todo_service.purge_deleted(service_db)
        assert count == 0

    @pytest.mark.asyncio
    async def test_purge_does_not_affect_active_todos(self, service_db):
        """Test that purge doesn't affect active todos."""
        data = TodoCreate(description="Active")
        created = await todo_service.create_todo(service_db, data)

        await todo_service.purge_deleted(service_db)

        result = await todo_service.get_todo(service_db, created.id)
        assert result is not None
