from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import verify_token
from app.database import get_db
from app.models.todo import (
    TodoCreate,
    TodoDeleteResponse,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services import todo_service

router = APIRouter()


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(data: TodoCreate, _: str = Depends(verify_token)):
    """Create a new TODO."""
    async with get_db() as db:
        return await todo_service.create_todo(db, data)


@router.get("", response_model=TodoListResponse)
async def list_todos(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[int] = Query(None, ge=1, le=4),
    _: str = Depends(verify_token),
):
    """List all TODOs with optional filters."""
    async with get_db() as db:
        todos = await todo_service.list_todos(db, status=status_filter, priority=priority)
        return TodoListResponse(todos=todos, count=len(todos))


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, _: str = Depends(verify_token)):
    """Get a single TODO by ID."""
    async with get_db() as db:
        todo = await todo_service.get_todo(db, todo_id)
        if todo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TODO not found",
            )
        return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, data: TodoUpdate, _: str = Depends(verify_token)):
    """Update a TODO."""
    async with get_db() as db:
        todo = await todo_service.update_todo(db, todo_id, data)
        if todo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TODO not found",
            )
        return todo


@router.delete("/{todo_id}", response_model=TodoDeleteResponse)
async def delete_todo(todo_id: int, _: str = Depends(verify_token)):
    """Soft delete a TODO."""
    async with get_db() as db:
        deleted = await todo_service.delete_todo(db, todo_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TODO not found",
            )
        return TodoDeleteResponse(message="TODO deleted", id=todo_id)


@router.post("/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(todo_id: int, _: str = Depends(verify_token)):
    """Mark a TODO as completed."""
    async with get_db() as db:
        todo = await todo_service.complete_todo(db, todo_id)
        if todo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TODO not found",
            )
        return todo


@router.post("/{todo_id}/reopen", response_model=TodoResponse)
async def reopen_todo(todo_id: int, _: str = Depends(verify_token)):
    """Reopen a completed TODO."""
    async with get_db() as db:
        todo = await todo_service.reopen_todo(db, todo_id)
        if todo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TODO not found",
            )
        return todo
