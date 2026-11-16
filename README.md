

# Repository Management System

A simplified GitHub-inspired, client-server repository management system built using Python and PostgreSQL.

The system allows multiple clients to connect to a centralized server over a LAN network, create repositories, manage collaborators, and perform repository-related operations through a command-line interface.

## Features

- **User Management:** User registration and authentication.
- **Repository Management:** Create, view and delete repositories.
- **Collaboration:** Add and remove repository collaborators.
- **Access Control:** Assign roles such as Owner, Developer and Viewer.
- **Branch Management:** Create and manage repository branches.
- **Commit Management:** Record commit messages and timestamps.
- **Issue Tracking:** Create and manage repository issues.
- **Pull Requests:** Create and review proposed changes.
- **Multi-client Support:** Allow multiple computers to access the same centralized system.

## Architecture

The application follows a three-tier client-server architecture.

```text
       Client PC 1             Client PC 2
      (Python CLI)             (Python CLI)
            |                       |
            |                       |
            +----------+------------+
                       |
                 HTTP / JSON
                       |
                Central Server
                  (FastAPI)
                       |
                 Database Layer
                       |
                  PostgreSQL
```

### Components

**1. Client**

- Provides a command-line interface.
- Accepts user commands.
- Sends HTTP requests to the server.
- Displays server responses.

**2. Server**

- Handles incoming client requests.
- Performs authentication and authorization.
- Implements application logic.
- Executes database operations.
- Returns responses in JSON format.

**3. Database**

- Stores users and repositories.
- Maintains relationships between repositories and collaborators.
- Stores branches, commits, issues and pull requests.
- Enforces relational integrity through constraints.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| Database Driver | Psycopg 3 |
| Client Interface | Python CLI |
| Communication | HTTP / JSON |
| Environment Manager | uv |

## Project Structure

```text
repository-management-system/
├── server/
│   ├── main.py
│   ├── database.py
│   ├── routes/
│   └── sql/
├── client/
│   ├── main.py
│   ├── commands.py
│   └── api.py
├── docs/
│   └── er_diagram.png
├── pyproject.toml
└── README.md
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL
- uv package manager

### 1. Clone the repository

```bash
git clone <repository-url>
cd repository-management-system
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure the database

Create a PostgreSQL database:

```sql
CREATE DATABASE scm_db;
```

Configure the database connection using environment variables.

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/scm_db"
```

### 4. Start the server

```bash
uv run uvicorn server.main:app --host 0.0.0.0 --port 8000
```

The server will be accessible at:

```text
http://SERVER_IP:8000
```

### 5. Start a client

On another computer connected to the same network:

```bash
uv run python -m client.main
```

Configure the client to connect to the server's LAN IP address.

## Database Concepts Demonstrated

This project demonstrates practical DBMS concepts, including:

- Entity Relationship modelling.
- Relational schema design.
- Database normalization (1NF, 2NF and 3NF).
- Primary and foreign keys.
- Unique, NOT NULL and CHECK constraints.
- One-to-many and many-to-many relationships.
- SQL joins and subqueries.
- Aggregate functions.
- Views.
- Stored functions and procedures.
- Triggers.
- Transactions and rollback.
- Indexing.
- Data integrity and access control.

## Communication Workflow

1. A client sends an HTTP request to the central server.
2. The server receives and validates the request.
3. The application executes the required database operation.
4. PostgreSQL processes the SQL query.
5. The server returns the result as a JSON response.
6. The client displays the result.

All clients access the same centralized database through the server.

## Project Objective

The primary objective is to demonstrate relational database design and implementation through a practical repository management application while exploring client-server communication and multi-user database access.

## Scope and Limitations

This project is an academic demonstration of a simplified repository management system.

It does not implement actual Git version control, source-code hosting, distributed storage or real-time collaboration.

---

**Academic Project:** Database Management Systems (DBMS)  
**Application Type:** Client-Server Application  
**Interface:** Command Line
