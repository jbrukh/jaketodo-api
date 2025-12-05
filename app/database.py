from typing import Optional

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings

DATABASE_PATH = settings.database_path


async def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the database with the todos table and indexes."""
    path = db_path or DATABASE_PATH

    # Ensure directory exists for file-based databases
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                due_date_text TEXT,
                due_date DATE,
                notes TEXT,
                priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 4),
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
                gcal_event_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                deleted_at TIMESTAMP
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_todos_status_deleted ON todos(status, deleted_at)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date)"
        )
        await db.commit()


@asynccontextmanager
async def get_db(db_path: Optional[str] = None):
    """Async context manager for database connections."""
    path = db_path or DATABASE_PATH
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
