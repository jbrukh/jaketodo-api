from fastapi import APIRouter, Depends

from app.auth import verify_token
from app.database import get_db
from app.models.todo import PurgeResponse
from app.services import todo_service

router = APIRouter()


@router.delete("/purge", response_model=PurgeResponse)
async def purge_deleted_todos(_: str = Depends(verify_token)):
    """Permanently delete all soft-deleted TODOs."""
    async with get_db() as db:
        count = await todo_service.purge_deleted(db)
        return PurgeResponse(message="Purged deleted TODOs", count=count)
