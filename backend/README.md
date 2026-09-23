# LexAssist API (Backend Prototype)

Backend API for the LexAssist legal assistance prototype.

## Purpose

Provides the HTTP API contract for the LexAssist frontend:

- Legal assistant prototype messaging
- Document template and prototype draft workflows
- Prototype legal research search
- Prototype case-history workspace records

This is a **prototype foundation**. All domain data is prototype/demo data.
There is no real AI and no authoritative legal content.
User authentication (register/login via Bearer JWT) is implemented.
The database does not contain authoritative legal sources.
The application is not production-ready.

## Architecture

```text
HTTP Route (app/api/routes)
    -> Pydantic Schema (app/schemas)
    -> Service (app/services)
    -> Repository (app/repositories)
    -> SQLAlchemy Session
    -> PostgreSQL
```

Routes never contain database queries. Services never contain SQLAlchemy
queries. Schemas stay separate from ORM models.

## Setup (Windows PowerShell)

### 1. PostgreSQL requirement

Install PostgreSQL 18 locally (project development default port: 5433)
and create the database and role:

```sql
CREATE USER lexassist WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE lexassist OWNER lexassist;
```

### 2. Virtual environment and dependencies

From the `backend/` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Environment configuration

```powershell
copy .env.example .env
```

Edit `.env` and set the real `DATABASE_URL` password. Never commit `.env`.

### 4. Alembic migration

```powershell
alembic upgrade head
```

### 5. Seed process

Inserts the explicit prototype/demo records (assistant conversation,
example document, research records, history items). No users, no secrets.

```powershell
python -m app.data.seed
```

### 6. Server startup

```powershell
uvicorn app.main:app --reload --port 8005
```

The API starts at `http://127.0.0.1:8005`.
Interactive docs: `http://127.0.0.1:8005/docs`.

### 7. Tests

Unit/integration tests use seeded SQLite and need no PostgreSQL server:

```powershell
pytest
```

## Database lifecycle

```text
Create database
    -> alembic upgrade head
    -> python -m app.data.seed
    -> uvicorn app.main:app --reload
```

Migrations under `alembic/versions/` are the schema authority.
`create_all()` is used only inside tests, never on application startup.
The seed script is idempotent and never runs automatically.

## Available endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/` | API info |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Register new user account |
| POST | `/api/v1/auth/login` | Authenticate and issue Bearer JWT |
| GET | `/api/v1/auth/me` | Current authenticated user profile |
| POST | `/api/v1/assistant/messages` | Prototype assistant reply (persisted) |
| GET | `/api/v1/assistant/conversations/{conversation_id}` | Prototype conversation |
| GET | `/api/v1/documents` | List prototype drafts |
| GET | `/api/v1/documents/templates` | List document templates |
| GET | `/api/v1/documents/{document_id}` | Prototype draft by id |
| POST | `/api/v1/documents` | Create persisted prototype draft |
| POST | `/api/v1/research/search` | Local prototype search |
| GET | `/api/v1/research/{result_id}` | Prototype record by id |
| GET | `/api/v1/history` | Prototype activity records |
| GET | `/api/v1/history/{item_id}` | Prototype record by id |

## Prototype limitations

- Assistant replies are fixed prototype text, not AI output.
- Document drafts are structured prototypes, not legally valid documents.
- Research records are labeled demo data, not authoritative sources.
- Persistence does not make prototype information authoritative.
- Business endpoints remain open; user authentication foundation is backend-only in this step.
