# API overview

Base URL: `http://localhost:8000`

## Auth

### POST /auth/login

```json
{ "email": "student@university.edu", "password": "Student123!" }
```

Returns JWT + user profile.

### POST /auth/logout

Requires `Authorization: Bearer <token>`. Client should discard the token.

### GET /auth/me

Returns the current user.

## Documents (admin)

### POST /documents/upload

`multipart/form-data` with `file` (PDF, max 25MB).

Indexing starts in the background.

### GET /documents

List uploaded documents and indexing status.

### DELETE /documents/{id}

Deletes the file and all related chunks.

### POST /documents/reindex

Rebuilds embeddings for every document.

## Chat

### POST /chat

```json
{ "question": "What is the tuition fee?", "stream": true }
```

Streaming response is Server-Sent Events:

- `{"type":"citations","citations":[...]}`
- `{"type":"token","content":"..."}`
- `{"type":"done","conversation_id":"..."}`

Set `stream: false` for a single JSON `ChatResponse`.

### GET /chat/history

Returns the authenticated user's recent Q&A pairs with citations.

## Health

### GET /health

Reports app, database, and NVIDIA API availability.
