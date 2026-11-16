"""Database connection and initialisation."""

import os
from pathlib import Path

import psycopg
from psycopg_pool import AsyncConnectionPool

_pool: AsyncConnectionPool | None = None

SQL_DIR = Path(__file__).parent.parent / "sql"
SQL_FILES = [
    "01_schema.sql",
    "02_views.sql",
    "03_functions.sql",
    "04_triggers.sql",
    "05_indexes.sql",
]


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url


async def get_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(get_db_url(), open=False)
        await _pool.open()
    return _pool


async def get_db():
    """FastAPI dependency — yields a psycopg async connection."""
    pool = await get_pool()
    async with pool.connection() as conn:
        yield conn


async def init_db() -> None:
    """Run all SQL migration files in order."""
    pool = await get_pool()
    async with pool.connection() as conn:
        for filename in SQL_FILES:
            sql = (SQL_DIR / filename).read_text()
            await conn.execute(sql)
        await conn.commit()


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
