# LexAssist

LexAssist is a legal-assistance prototype with guided document workflows,
prototype legal-research search, and a case-history workspace.

## Architecture

Frontend:
React + TypeScript + Vite

Backend:
FastAPI + SQLAlchemy + Alembic

Database:
PostgreSQL 18 (each developer runs their own local instance)

## Repository Structure

```text
LexAI/
├── frontend/          React + TypeScript + Vite app
├── backend/           FastAPI API, SQLAlchemy models, Alembic migrations
├── .gitignore
└── README.md
```

## Prerequisites

| Tool       | Version required / recommended                  |
| ---------- | ----------------------------------------------- |
| Node.js    | 22.x (verified: v22.12.0)                       |
| npm        | 10.x (verified: 10.9.0)                         |
| Python     | 3.12.x (verified: 3.12.6)                       |
| PostgreSQL | 18, running locally                             |
| Git        | any recent version                              |

## 1. Clone

```powershell
git clone https://github.com/rajiv9595/LexAI
cd LexAI
```

> `YOUR_GITHUB_REPOSITORY_URL` is a placeholder. The repository owner will
> share the real URL after creating the GitHub repository.

## 2. Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Create your own local environment file from the committed example:

```powershell
copy .env.example .env
```

Then edit `backend/.env` and set **your own** values:

- your own PostgreSQL password inside `DATABASE_URL`
- your own long random `JWT_SECRET_KEY`

Never copy another developer's `.env`. Never commit `.env`.

## 3. PostgreSQL setup (local to YOUR laptop)

PostgreSQL is **local** to each developer's laptop. Nobody connects to
anyone else's database.

Create your own role and database. The project development default is
PostgreSQL 18 on port **5433**, database `lexassist`, role `lexassist`:

```sql
CREATE USER lexassist WITH PASSWORD 'YOUR_OWN_PASSWORD';
CREATE DATABASE lexassist OWNER lexassist;
```

Make sure `DATABASE_URL` in your `backend/.env` points at **your**
instance, for example conceptually:

```text
postgresql+psycopg://lexassist:YOUR_OWN_PASSWORD@localhost:5433/lexassist
```

> If port 5433 is already taken on your machine, use a free port and put
> that port in your own `backend/.env`. Nothing else in the repo needs to
> change. Never point your `.env` at a teammate's laptop.

## 4. Database initialization

Run these in order from the `backend/` directory.
Each developer runs them against **their own** database:

```powershell
cd backend
alembic upgrade head
python -m app.data.seed
```

What each step does:

1. `alembic upgrade head` — creates the complete schema
   (prototype tables + user/authentication tables) from the migration
   chain under `backend/alembic/versions/`.
2. `python -m app.data.seed` — loads deterministic prototype/demo
   records (demo conversation, example document, research records,
   history items). The seed is idempotent: running it twice inserts
   nothing the second time. It creates **no users and no credentials**.

Then start the backend:

```powershell
uvicorn app.main:app --reload --port 8005
```

Port **8005** is the project development default for the backend
(the frontend is preconfigured to call it). The project intentionally
does not use port 8000, which is commonly occupied by other local
services. If you must use a different backend port, update
`VITE_API_BASE_URL` in your own `frontend/.env` to match.

API docs: `http://localhost:8005/docs`

## 5. Frontend setup

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

`frontend/.env` must point at **your** backend:

```text
VITE_API_BASE_URL=http://localhost:8005
```

If you changed the backend port (see above), change this URL to match.

## 6. Run both

Terminal 1 (backend):

```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8005
```

Terminal 2 (frontend):

```powershell
cd frontend
npm run dev
```

Browser:

```text
http://localhost:5173
```

Log in / register through the app. Authentication is backed by the JWT
issued by **your** local backend against **your** local database.

## Important: Database Is Local

GitHub stores the application source code and the database migration
definitions. GitHub does **NOT** store the live PostgreSQL database.

Every developer has their own independent local PostgreSQL database:

```text
Developer A  →  PostgreSQL on Laptop A
Developer B  →  PostgreSQL on Laptop B
Developer C  →  PostgreSQL on Laptop C
```

All developers share the same:

- source code
- Alembic migrations
- seed logic

but each has an independent database with their own password and JWT
secret. The project never depends on one person's laptop.

## Team Workflow

`main` is the shared branch. Do not commit directly to it for day-to-day
work — use short-lived feature branches:

```text
main
│
├── feature/frontend-...
├── feature/backend-...
├── feature/research-...
└── feature/ai-...
```

Before starting new work, pull the latest `main`:

```powershell
git checkout main
git pull
git checkout -b feature/my-change
```

Work, then push and open a Pull Request:

```powershell
git add .
git commit -m "Describe the change"
git push -u origin feature/my-change
```

Then create a Pull Request into `main` on GitHub for review.

## Important Database Team Rules

NEVER share or commit:

- PostgreSQL passwords
- `backend/.env` / `frontend/.env`
- JWT secrets
- database dumps containing private data
- production credentials

If a teammate needs data: they run migrations + seed data.
If the schema changes: commit an Alembic migration — never ask teammates
to manually recreate tables, and never manually modify the PostgreSQL
schema and expect GitHub to know about it.

## Development Ports (defaults)

| Service    | Default           |
| ---------- | ----------------- |
| Frontend   | `http://localhost:5173` |
| Backend    | `http://localhost:8005` |
| PostgreSQL | `localhost:5433`  |

These are development defaults. If another process occupies one of these
ports on your laptop, change it locally:

- Backend port change → also update `VITE_API_BASE_URL` in your own
  `frontend/.env`.
- PostgreSQL port change → also update `DATABASE_URL` in your own
  `backend/.env`.

## Team Database Schema Workflow

When the database schema changes:

1. Modify the SQLAlchemy model.
2. Create an Alembic migration (`alembic revision --autogenerate -m "..."`).
3. Test the migration (`alembic upgrade head`, and `downgrade` if needed).
4. Commit the migration file and push the branch.
5. Teammates pull and run:

```powershell
alembic upgrade head
```

Migration files under `backend/alembic/versions/` are the schema
authority. Never ask teammates to manually recreate tables.
