from datetime import datetime
from typing import List, Optional

import aiosqlite

from app.models.todo import TodoCreate, TodoResponse, TodoUpdate


def _row_to_todo(row: aiosqlite.Row) -> TodoResponse:
    """Convert a database row to a TodoResponse."""
    return TodoResponse(
        id=row["id"],
        description=row["description"],
        due_date_text=row["due_date_text"],
        due_date=row["due_date"],
        notes=row["notes"],
        priority=row["priority"],
        status=row["status"],
        gcal_event_id=row["gcal_event_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )


async def create_todo(db: aiosqlite.Connection, data: TodoCreate) -> TodoResponse:
    """Create a new TODO."""
    cursor = await db.execute(
        """
        INSERT INTO todos (description, due_date_text, due_date, notes, priority, gcal_event_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.description,
            data.due_date_text,
            data.due_date.isoformat() if data.due_date else None,
            data.notes,
            data.priority,
            data.gcal_event_id,
        ),
    )
    await db.commit()

    todo_id = cursor.lastrowid
    return await get_todo(db, todo_id)


async def get_todo(db: aiosqlite.Connection, todo_id: int) -> Optional[TodoResponse]:
    """Get a single TODO by ID (excludes deleted)."""
    cursor = await db.execute(
        "SELECT * FROM todos WHERE id = ? AND deleted_at IS NULL",
        (todo_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_todo(row)


async def list_todos(
    db: aiosqlite.Connection,
    status: Optional[str] = None,
    priority: Optional[int] = None,
) -> List[TodoResponse]:
    """List TODOs with optional filters, sorted by due_date (NULLs last) then priority."""
    query = "SELECT * FROM todos WHERE deleted_at IS NULL"
    params: List = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    # Sort by due_date ascending (NULLs last), then priority ascending
    query += " ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC, priority ASC"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [_row_to_todo(row) for row in rows]


async def update_todo(
    db: aiosqlite.Connection, todo_id: int, data: TodoUpdate
) -> Optional[TodoResponse]:
    """Update a TODO with partial data."""
    # First check if TODO exists and is not deleted
    existing = await get_todo(db, todo_id)
    if existing is None:
        return None

    # Build update query dynamically based on provided fields
    updates = []
    params = []

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "due_date" and value is not None:
            value = value.isoformat()
        updates.append(f"{field} = ?")
        params.append(value)

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(todo_id)

        query = f"UPDATE todos SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL"
        await db.execute(query, params)
        await db.commit()

    return await get_todo(db, todo_id)


async def delete_todo(db: aiosqlite.Connection, todo_id: int) -> bool:
    """Soft delete a TODO by setting deleted_at."""
    # Check if TODO exists and is not already deleted
    existing = await get_todo(db, todo_id)
    if existing is None:
        return False

    await db.execute(
        "UPDATE todos SET deleted_at = ?, updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), todo_id),
    )
    await db.commit()
    return True


async def complete_todo(db: aiosqlite.Connection, todo_id: int) -> Optional[TodoResponse]:
    """Mark a TODO as completed."""
    existing = await get_todo(db, todo_id)
    if existing is None:
        return None

    now = datetime.utcnow().isoformat()
    await db.execute(
        "UPDATE todos SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
        (now, now, todo_id),
    )
    await db.commit()
    return await get_todo(db, todo_id)


async def reopen_todo(db: aiosqlite.Connection, todo_id: int) -> Optional[TodoResponse]:
    """Reopen a completed TODO."""
    existing = await get_todo(db, todo_id)
    if existing is None:
        return None

    now = datetime.utcnow().isoformat()
    await db.execute(
        "UPDATE todos SET status = 'pending', completed_at = NULL, updated_at = ? WHERE id = ?",
        (now, todo_id),
    )
    await db.commit()
    return await get_todo(db, todo_id)


async def purge_deleted(db: aiosqlite.Connection) -> int:
    """Permanently delete all soft-deleted TODOs. Returns count of purged items."""
    cursor = await db.execute("SELECT COUNT(*) FROM todos WHERE deleted_at IS NOT NULL")
    row = await cursor.fetchone()
    count = row[0]

    await db.execute("DELETE FROM todos WHERE deleted_at IS NOT NULL")
    await db.commit()

    return count
