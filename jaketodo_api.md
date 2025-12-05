# JakeTodo API Guide for Claude

## Overview

This is a REST API for managing TODOs. Use this API to create, read, update, delete, complete, and reopen TODO items.

## Base URL

```
https://jaketodo-api-production.up.railway.app
```

## Authentication

All endpoints except `/health` require a Bearer token in the Authorization header:

```
Authorization: Bearer <JAKETODO_API_TOKEN>
```

Load the token from the credentials file.

## Endpoints

### Health Check (No Auth Required)

```
GET /health
```

Response: `{"status": "healthy"}`

---

### List TODOs

```
GET /todos
```

Query parameters (optional):
- `status`: Filter by `pending` or `completed`
- `priority`: Filter by priority (1=urgent, 2=high, 3=normal, 4=low)

Response:
```json
{
  "todos": [...],
  "count": 5
}
```

---

### Create TODO

```
POST /todos
Content-Type: application/json
```

Request body:
```json
{
  "description": "Review PR for auth module",
  "due_date_text": "next Friday",
  "due_date": "2025-01-17",
  "notes": "Check the token refresh logic",
  "priority": 2,
  "gcal_event_id": "optional_calendar_id"
}
```

Required: `description`
Optional: `due_date_text`, `due_date`, `notes`, `priority` (default 3), `gcal_event_id`

Priority levels: 1=urgent, 2=high, 3=normal, 4=low

---

### Bulk Create TODOs

```
POST /todos/bulk
Content-Type: application/json
```

Request body:
```json
{
  "todos": [
    {
      "description": "First task",
      "priority": 1
    },
    {
      "description": "Second task",
      "due_date": "2025-01-20",
      "priority": 2
    },
    {
      "description": "Third task",
      "notes": "Some notes",
      "priority": 3
    }
  ]
}
```

Required: `todos` array with at least one TODO (each requiring `description`)

Response:
```json
{
  "todos": [...],
  "count": 3
}
```

---

### Get Single TODO

```
GET /todos/{id}
```

---

### Update TODO

```
PUT /todos/{id}
Content-Type: application/json
```

Request body (all fields optional):
```json
{
  "description": "Updated description",
  "due_date_text": "tomorrow",
  "due_date": "2025-01-16",
  "notes": "Updated notes",
  "priority": 1,
  "gcal_event_id": "new_event_id"
}
```

---

### Delete TODO (Soft Delete)

```
DELETE /todos/{id}
```

Response: `{"message": "TODO deleted", "id": 1}`

---

### Mark TODO Complete

```
POST /todos/{id}/complete
```

Sets status to "completed" and records completion timestamp.

---

### Reopen TODO

```
POST /todos/{id}/reopen
```

Sets status back to "pending" and clears completion timestamp.

---

### Purge Deleted TODOs (Admin)

```
DELETE /admin/purge
```

Permanently removes all soft-deleted TODOs.

Response: `{"message": "Purged deleted TODOs", "count": 5}`

---

## Example Commands

### List all pending TODOs
```bash
curl -H "Authorization: Bearer $JAKETODO_API_TOKEN" \
  "https://jaketodo-api-production.up.railway.app/todos?status=pending"
```

### Create a TODO
```bash
curl -X POST \
  -H "Authorization: Bearer $JAKETODO_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Buy groceries", "priority": 2}' \
  "https://jaketodo-api-production.up.railway.app/todos"
```

### Complete a TODO
```bash
curl -X POST \
  -H "Authorization: Bearer $JAKETODO_API_TOKEN" \
  "https://jaketodo-api-production.up.railway.app/todos/1/complete"
```

### Bulk Create TODOs
```bash
curl -X POST \
  -H "Authorization: Bearer $JAKETODO_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"todos": [{"description": "Task 1"}, {"description": "Task 2", "priority": 1}]}' \
  "https://jaketodo-api-production.up.railway.app/todos/bulk"
```

---

## Natural Language Mappings

| User Says | API Action |
|-----------|------------|
| "Add a TODO to..." | POST /todos |
| "Add these TODOs: X, Y, Z" | POST /todos/bulk |
| "Create multiple tasks: ..." | POST /todos/bulk |
| "Remind me to X by Friday" | POST /todos with due_date_text and due_date |
| "Show my TODOs" | GET /todos |
| "What's urgent?" | GET /todos?priority=1 |
| "Show completed tasks" | GET /todos?status=completed |
| "Mark TODO 5 as done" | POST /todos/5/complete |
| "Reopen TODO 3" | POST /todos/3/reopen |
| "Delete TODO 7" | DELETE /todos/7 |
| "Update TODO 2 priority to high" | PUT /todos/2 with priority=2 |
