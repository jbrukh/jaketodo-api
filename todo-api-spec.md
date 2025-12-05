# TODO API — Specification

## Overview

A minimal Python/FastAPI REST API for single-user TODO management. Uses SQLite on Railway with persistent storage. Designed for Claude Skill integration.

**Key Features:**
- Create, read, update, delete TODOs (soft delete)
- Natural language due dates + parsed DATE for sorting
- Priority levels (1-4, with 1 being highest)
- Optional notes field
- Optional Google Calendar event ID reference
- Filter by status and priority
- Sort by due date, then priority

---

## Database Schema

### `todos`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `description` | TEXT NOT NULL | The TODO item text |
| `due_date_text` | TEXT NULL | Natural language due date (e.g., "next Friday") |
| `due_date` | DATE NULL | Parsed date for sorting (AI fills this in) |
| `notes` | TEXT NULL | Additional notes |
| `priority` | INTEGER NOT NULL DEFAULT 3 | 1=urgent, 2=high, 3=normal, 4=low |
| `status` | TEXT NOT NULL DEFAULT 'pending' | 'pending' or 'completed' |
| `gcal_event_id` | TEXT NULL | Google Calendar event ID reference |
| `created_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Last update |
| `completed_at` | TIMESTAMP NULL | When marked complete |
| `deleted_at` | TIMESTAMP NULL | Soft delete timestamp (NULL = active) |

**Indexes**: `(status, deleted_at)`, `(priority)`, `(due_date)`

---

## API Endpoints

### Authentication

All endpoints (except `/health`) require header:
```
Authorization: Bearer <API_TOKEN>
```

---

### TODOs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/todos` | Create a TODO |
| `GET` | `/todos` | List TODOs (excludes deleted) |
| `GET` | `/todos/{id}` | Get single TODO |
| `PUT` | `/todos/{id}` | Update TODO |
| `DELETE` | `/todos/{id}` | Soft delete TODO |
| `POST` | `/todos/{id}/complete` | Mark as complete |
| `POST` | `/todos/{id}/reopen` | Mark as pending again |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `DELETE` | `/admin/purge` | Permanently delete all soft-deleted TODOs |

---

### Endpoint Details

**POST `/todos`** — Create a TODO

Request:
```json
{
  "description": "Review PR for auth module",
  "due_date_text": "end of week",
  "due_date": "2025-01-17",
  "notes": "Check the token refresh logic",
  "priority": 2,
  "gcal_event_id": "abc123xyz"
}
```

Response (201):
```json
{
  "id": 1,
  "description": "Review PR for auth module",
  "due_date_text": "end of week",
  "due_date": "2025-01-17",
  "notes": "Check the token refresh logic",
  "priority": 2,
  "status": "pending",
  "gcal_event_id": "abc123xyz",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "completed_at": null
}
```

---

**GET `/todos`** — List TODOs

Query parameters:
- `status` (optional): `pending` or `completed`
- `priority` (optional): `1`, `2`, `3`, or `4`

**Default sort order**: `due_date` ascending (NULLs last), then `priority` ascending (1=urgent first)

Response (200):
```json
{
  "todos": [
    {
      "id": 1,
      "description": "Review PR for auth module",
      "due_date_text": "end of week",
      "due_date": "2025-01-17",
      "notes": "Check the token refresh logic",
      "priority": 2,
      "status": "pending",
      "gcal_event_id": "abc123xyz",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z",
      "completed_at": null
    }
  ],
  "count": 1
}
```

---

**GET `/todos/{id}`** — Get single TODO

Response (200): Single TODO object

Response (404): `{"detail": "TODO not found"}`

---

**PUT `/todos/{id}`** — Update TODO

Request (all fields optional):
```json
{
  "description": "Review PR for auth module - URGENT",
  "due_date_text": "tomorrow",
  "due_date": "2025-01-16",
  "notes": "Updated notes",
  "priority": 1,
  "gcal_event_id": "new_event_id"
}
```

Response (200): Updated TODO object

---

**DELETE `/todos/{id}`** — Soft delete TODO

Response (200):
```json
{
  "message": "TODO deleted",
  "id": 1
}
```

---

**POST `/todos/{id}/complete`** — Mark as complete

Response (200): Updated TODO object with `status: "completed"` and `completed_at` set

---

**POST `/todos/{id}/reopen`** — Reopen TODO

Response (200): Updated TODO object with `status: "pending"` and `completed_at: null`

---

**DELETE `/admin/purge`** — Permanently delete soft-deleted TODOs

Response (200):
```json
{
  "message": "Purged deleted TODOs",
  "count": 5
}
```

---

## Project Structure

```
todo-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, middleware, startup
│   ├── config.py            # Settings (env vars)
│   ├── auth.py              # API token dependency
│   ├── database.py          # SQLite connection, schema init
│   ├── models/
│   │   ├── __init__.py
│   │   └── todo.py          # TODO Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── todos.py         # TODO endpoints
│   │   └── admin.py         # Admin endpoints
│   └── services/
│       ├── __init__.py
│       └── todo_service.py  # TODO business logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures, test DB setup
│   ├── test_todos.py        # TODO endpoint tests
│   ├── test_todo_service.py # Service unit tests
│   └── test_auth.py         # Auth tests
├── requirements.txt
├── Dockerfile
├── railway.toml
└── README.md
```

---

## Implementation Plan

### Phase 1: Project Foundation
**Goal**: Working FastAPI app with SQLite connection and auth

**Tasks**:
1. Create project directory structure
2. Create `requirements.txt`:
   ```
   fastapi==0.109.0
   uvicorn[standard]==0.27.0
   pydantic==2.5.3
   pydantic-settings==2.1.0
   aiosqlite==0.19.0
   pytest==7.4.4
   pytest-asyncio==0.23.3
   pytest-cov==4.1.0
   httpx==0.26.0
   ```
3. Implement `app/config.py`:
   - Load `API_TOKEN` and `DATABASE_PATH` from environment
   - Default `DATABASE_PATH` to `./data/todos.db`
4. Implement `app/database.py`:
   - Async SQLite connection using `aiosqlite`
   - `init_db()` function that creates the `todos` table
   - `get_db()` async context manager
5. Implement `app/auth.py`:
   - FastAPI `Depends` that validates `Authorization: Bearer <token>`
   - Raise `HTTPException(401)` if invalid
6. Implement `app/main.py`:
   - Create FastAPI app with title "TODO API"
   - Startup event to call `init_db()`
   - `/health` endpoint (no auth)
   - CORS middleware
7. Create `Dockerfile`:
   - Use `python:3.11-slim`
   - Create `/data` directory for SQLite
   - Run with `uvicorn`
8. Create `railway.toml`
9. Write tests:
   - `/health` returns 200
   - Protected endpoint returns 401 without token
   - Protected endpoint returns 401 with wrong token

### Phase 2: TODO CRUD
**Goal**: Create, read, update, delete TODOs

**Tasks**:
1. Create `app/models/todo.py`:
   - `TodoCreate` — description required, others optional
   - `TodoUpdate` — all fields optional
   - `TodoResponse` — full TODO with all fields
   - `TodoListResponse` — list with count
2. Implement `app/services/todo_service.py`:
   - `create_todo(data)` — insert new TODO
   - `get_todo(id)` — fetch by ID (exclude deleted)
   - `list_todos(status=None, priority=None)` — list with filters, sorted by due_date then priority
   - `update_todo(id, data)` — partial update, set updated_at
   - `delete_todo(id)` — set `deleted_at` timestamp
3. Implement `app/routers/todos.py`:
   - `POST /todos`
   - `GET /todos`
   - `GET /todos/{id}`
   - `PUT /todos/{id}`
   - `DELETE /todos/{id}`
4. Register router in `main.py`
5. Write tests:
   - Create TODO with all fields
   - Create TODO with only description
   - List all TODOs
   - List filtered by status
   - List filtered by priority
   - Verify sort order (due_date, then priority)
   - Get single TODO
   - Get non-existent TODO returns 404
   - Update TODO
   - Partial update TODO
   - Delete TODO (soft)
   - Deleted TODO not returned in list
   - Deleted TODO returns 404 on get

### Phase 3: Status Actions
**Goal**: Complete and reopen TODOs

**Tasks**:
1. Add to `app/services/todo_service.py`:
   - `complete_todo(id)` — set status to completed, set completed_at
   - `reopen_todo(id)` — set status to pending, clear completed_at
2. Add to `app/routers/todos.py`:
   - `POST /todos/{id}/complete`
   - `POST /todos/{id}/reopen`
3. Write tests:
   - Complete a pending TODO
   - Complete sets completed_at timestamp
   - Reopen a completed TODO
   - Reopen clears completed_at
   - Complete already-completed TODO (idempotent)
   - Reopen already-pending TODO (idempotent)
   - Complete deleted TODO returns 404

### Phase 4: Admin & Polish
**Goal**: Admin operations, error handling, final touches

**Tasks**:
1. Implement `app/routers/admin.py`:
   - `DELETE /admin/purge` — permanently delete all soft-deleted TODOs, return count
2. Register router in `main.py`
3. Add global exception handler for consistent error responses
4. Ensure proper OpenAPI documentation with tags
5. Write tests:
   - Purge removes soft-deleted TODOs
   - Purge returns correct count
   - Purge does not affect active TODOs

---

## Testing Strategy

### Tools
- `pytest` — test framework
- `pytest-asyncio` — async test support
- `httpx` — async HTTP client for API tests
- `pytest-cov` — coverage reporting

### Test Database
- Each test uses a fresh in-memory SQLite database (`:memory:`)
- Fixtures in `conftest.py` provide:
  - `test_db` — initialized database
  - `test_client` — FastAPI TestClient with auth header
  - `sample_todo` — a basic TODO for testing

### Coverage Target
- **100% coverage required**
- Run with: `pytest --cov=app --cov-report=term-missing --cov-fail-under=100`

### Test Files

**`tests/test_auth.py`**:
- Missing auth header returns 401
- Invalid token returns 401
- Valid token allows access

**`tests/test_todos.py`**:
- All CRUD operations
- All filter combinations
- Sort order verification
- All status transitions
- Edge cases (not found, already deleted)
- Validation errors (invalid priority, empty description)

**`tests/test_todo_service.py`**:
- Unit tests for service functions
- Database interaction tests

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_TOKEN` | Bearer token for authentication | — | Yes |
| `DATABASE_PATH` | Path to SQLite database file | `./data/todos.db` | No |

---

## Deployment Steps

### 1. Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=100

# Run locally
export API_TOKEN=dev_token
export DATABASE_PATH=./data/todos.db
uvicorn app.main:app --reload
```

### 2. Docker Build
```bash
docker build -t todo-api .
docker run -p 8000:8000 \
  -e API_TOKEN=test \
  -v $(pwd)/data:/data \
  todo-api
```

### 3. Railway Deployment

1. Create new Railway project
2. Add persistent volume mounted at `/data`
3. Set environment variables:
   - `API_TOKEN` — generate a secure token
   - `DATABASE_PATH` — `/data/todos.db`
4. Deploy via Railway CLI or GitHub integration:
   ```bash
   railway login
   railway link
   railway up
   ```
5. Verify deployment:
   ```bash
   curl https://your-app.railway.app/health
   ```

### 4. Post-Deployment Verification
- Test `/health` endpoint
- Test creating a TODO
- Test listing TODOs
- Test completing a TODO
- Verify auth rejection without token

---

## SQLite Schema SQL

```sql
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
);

CREATE INDEX IF NOT EXISTS idx_todos_status_deleted ON todos(status, deleted_at);
CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority);
CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date);
```

---

## Claude Skill Example Commands

| Natural Language | API Translation |
|------------------|-----------------|
| "Add a TODO to review the PR" | `POST /todos` with description |
| "Remind me to call Mom by Friday" | `POST /todos` with due_date_text "Friday", due_date "2025-01-17" |
| "Show my TODOs" | `GET /todos` |
| "What's urgent?" | `GET /todos?priority=1` |
| "Show completed tasks" | `GET /todos?status=completed` |
| "Mark TODO 5 as done" | `POST /todos/5/complete` |
| "Reopen TODO 3" | `POST /todos/3/reopen` |
| "Delete TODO 7" | `DELETE /todos/7` |
| "Update TODO 2 to high priority" | `PUT /todos/2` with priority=2 |

---

*End of Specification*
