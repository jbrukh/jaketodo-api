import os
import tempfile
from contextlib import asynccontextmanager

import aiosqlite
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set environment variables before importing app modules
os.environ["JAKETODO_API_TOKEN"] = "test_token"
os.environ["DATABASE_PATH"] = ":memory:"

from app.database import init_db
from app.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def test_db():
    """Create a fresh temporary database for each test."""
    # Use a temp file for the database so connections share state
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    await init_db(db_path)

    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
        # Clean up temp file
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest_asyncio.fixture
async def test_client(test_db):
    """Create a test client with auth headers and mocked database."""

    @asynccontextmanager
    async def mock_get_db(db_path=None):
        yield test_db

    # Patch get_db to use our test database
    import app.routers.todos as todos_module
    import app.routers.admin as admin_module

    original_todos_get_db = todos_module.get_db
    original_admin_get_db = admin_module.get_db

    todos_module.get_db = mock_get_db
    admin_module.get_db = mock_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer test_token"},
        ) as client:
            yield client
    finally:
        todos_module.get_db = original_todos_get_db
        admin_module.get_db = original_admin_get_db


@pytest_asyncio.fixture
async def unauthenticated_client():
    """Create a test client without auth headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def sample_todo(test_client):
    """Create a sample TODO for testing."""
    response = await test_client.post(
        "/todos",
        json={
            "description": "Test TODO",
            "due_date_text": "tomorrow",
            "due_date": "2025-01-15",
            "notes": "Test notes",
            "priority": 2,
        },
    )
    return response.json()
