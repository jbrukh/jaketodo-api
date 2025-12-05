from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """Schema for creating a new TODO."""

    description: str = Field(..., min_length=1)
    due_date_text: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=4)
    gcal_event_id: Optional[str] = None


class TodoUpdate(BaseModel):
    """Schema for updating a TODO. All fields are optional."""

    description: Optional[str] = Field(default=None, min_length=1)
    due_date_text: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=4)
    gcal_event_id: Optional[str] = None


class TodoResponse(BaseModel):
    """Schema for TODO response."""

    id: int
    description: str
    due_date_text: Optional[str]
    due_date: Optional[date]
    notes: Optional[str]
    priority: int
    status: str
    gcal_event_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class TodoListResponse(BaseModel):
    """Schema for list of TODOs response."""

    todos: List[TodoResponse]
    count: int


class TodoDeleteResponse(BaseModel):
    """Schema for TODO deletion response."""

    message: str
    id: int


class PurgeResponse(BaseModel):
    """Schema for purge response."""

    message: str
    count: int
