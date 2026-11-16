"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.database import close_db, init_db
from server.routes import branches, commits, issues, repos, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="Repository Management System", lifespan=lifespan)

app.include_router(users.router)
app.include_router(repos.router)
app.include_router(branches.router)
app.include_router(commits.router)
app.include_router(issues.router)


@app.get("/")
async def root():
    return {"message": "Repository Management System API", "version": "1.0.0"}
