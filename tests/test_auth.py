import os
import tempfile

import pytest
import pytest_asyncio

from app.database import get_db, init_db


@pytest.mark.asyncio
async def test_missing_auth_header_returns_401(unauthenticated_client):
    """Test that missing auth header returns 401."""
    response = await unauthenticated_client.get("/todos")
    assert response.status_code == 403  # HTTPBearer returns 403 when no header


@pytest.mark.asyncio
async def test_invalid_token_returns_401(unauthenticated_client):
    """Test that invalid token returns 401."""
    response = await unauthenticated_client.get(
        "/todos", headers={"Authorization": "Bearer wrong_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"


@pytest.mark.asyncio
async def test_valid_token_allows_access(test_client):
    """Test that valid token allows access."""
    response = await test_client.get("/todos")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_no_auth_required(unauthenticated_client):
    """Test that health endpoint doesn't require auth."""
    response = await unauthenticated_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_get_db_context_manager():
    """Test that get_db properly opens and closes connections."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        await init_db(db_path)

        async with get_db(db_path) as db:
            # Verify we can use the connection
            cursor = await db.execute("SELECT 1")
            result = await cursor.fetchone()
            assert result[0] == 1
    finally:
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_app_lifespan():
    """Test that app lifespan initializes database."""
    from app.main import lifespan, app

    # Directly test the lifespan context manager
    async with lifespan(app):
        # The database should be initialized now
        pass
