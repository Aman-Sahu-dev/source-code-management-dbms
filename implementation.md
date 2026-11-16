# Implementation Plan — Repository Management System

A simple GitHub-inspired client-server app using FastAPI + PostgreSQL + CLI.

---

## Project Structure

```
dbms-scm/
├── server/
│   ├── main.py        # FastAPI app + route registration
│   ├── database.py    # psycopg3 connection + init_db()
│   ├── auth.py        # password hashing + token store
│   ├── models.py      # Pydantic schemas
│   └── routes/
│       ├── users.py
│       ├── repos.py
│       ├── branches.py
│       ├── commits.py
│       └── issues.py
├── client/
│   ├── main.py        # Typer CLI entry point
│   ├── api.py         # httpx wrapper (attaches token header)
│   └── config.py      # saves server URL + token to ~/.dbms-scm/config.json
├── sql/
│   ├── 01_schema.sql  # tables + constraints
│   ├── 02_views.sql   # useful views
│   ├── 03_functions.sql # stored functions
│   ├── 04_triggers.sql  # triggers
│   └── 05_indexes.sql   # indexes
├── .env.example
└── pyproject.toml
```

---

## Database (sql/)

### Tables

| Table | Columns |
|---|---|
| `users` | id, username (UNIQUE), email (UNIQUE), password_hash, created_at |
| `repositories` | id, name, description, owner_id (FK→users), is_private, created_at |
| `collaborators` | repo_id (FK), user_id (FK), role ('owner'/'developer'/'viewer'), PK(repo_id,user_id) |
| `branches` | id, repo_id (FK), name, created_by (FK→users), created_at |
| `commits` | id, branch_id (FK), author_id (FK→users), message, committed_at |
| `issues` | id, repo_id (FK), author_id (FK→users), title, body, status ('open'/'closed'), created_at |

### Advanced SQL Features
- **Views:** `repo_summary` (repo + owner + commit count + issue count)
- **Stored Function:** `get_repo_stats(repo_id)` returns commit + issue counts
- **Stored Procedure:** `close_issue(issue_id)` sets status = 'closed'
- **Trigger:** after INSERT on `repositories` → auto-insert owner into `collaborators` as 'owner'
- **Indexes:** on `commits.branch_id`, `issues.repo_id`, `repositories.owner_id`
- **Transactions:** delete repo wrapped in a transaction (cascades branches, commits, issues)

---

## Server (FastAPI)

**Auth:** token = `sha256(username:secret)` stored in a server-side dict. Passed via `X-Token` header.

### Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/users/register` | create account |
| POST | `/users/login` | get token |
| POST | `/users/logout` | invalidate token |
| GET | `/repos` | list repos you can see |
| POST | `/repos` | create repo |
| GET | `/repos/{id}` | repo details (uses view) |
| DELETE | `/repos/{id}` | delete repo (owner only, transaction) |
| GET | `/repos/{id}/branches` | list branches |
| POST | `/repos/{id}/branches` | create branch |
| GET | `/repos/{id}/branches/{bid}/commits` | list commits |
| POST | `/repos/{id}/branches/{bid}/commits` | add commit |
| GET | `/repos/{id}/issues` | list issues |
| POST | `/repos/{id}/issues` | create issue |
| PATCH | `/repos/{id}/issues/{iid}` | close issue (calls procedure) |

---

## Client (Typer CLI)

```
scm config set-server <url>
scm auth register
scm auth login
scm auth logout

scm repo list
scm repo create <name>
scm repo view <id>
scm repo delete <id>

scm branch list <repo-id>
scm branch create <repo-id> <name>

scm commit list <repo-id> <branch-id>
scm commit add <repo-id> <branch-id>

scm issue list <repo-id>
scm issue create <repo-id>
scm issue close <repo-id> <issue-id>
```

Output with `rich` tables. Errors printed in red.

---

## Dependencies

```toml
fastapi, uvicorn, psycopg[binary], psycopg-pool,
httpx, typer, rich, python-dotenv
```

---

## Build Order

1. `sql/` files (schema → views → functions → triggers → indexes)
2. `server/database.py` → `server/auth.py` → `server/models.py`
3. `server/routes/*` → `server/main.py`
4. `client/config.py` → `client/api.py` → `client/main.py`
5. `pyproject.toml` + `.env.example`
