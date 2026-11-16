-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_private BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(owner_id, name)
);

-- Collaborators (many-to-many: repos <-> users)
CREATE TABLE IF NOT EXISTS collaborators (
    repo_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('owner', 'developer', 'viewer')),
    PRIMARY KEY (repo_id, user_id)
);

-- Branches
CREATE TABLE IF NOT EXISTS branches (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(repo_id, name)
);

-- Commits
CREATE TABLE IF NOT EXISTS commits (
    id SERIAL PRIMARY KEY,
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Issues
CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    body TEXT,
    status VARCHAR(10) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
