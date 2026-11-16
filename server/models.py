"""Pydantic request and response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Users ────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


class TokenOut(BaseModel):
    token: str
    username: str


# ── Repositories ─────────────────────────────────────────────────────────────

class RepoCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class RepoOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_private: bool
    owner_id: int
    owner_username: str
    created_at: datetime
    commit_count: int = 0
    open_issue_count: int = 0


# ── Branches ─────────────────────────────────────────────────────────────────

class BranchCreate(BaseModel):
    name: str


class BranchOut(BaseModel):
    id: int
    repo_id: int
    name: str
    created_by: int
    created_at: datetime


# ── Commits ───────────────────────────────────────────────────────────────────

class CommitCreate(BaseModel):
    message: str


class CommitOut(BaseModel):
    id: int
    branch_id: int
    author_id: int
    author_username: str
    message: str
    committed_at: datetime


# ── Issues ────────────────────────────────────────────────────────────────────

class IssueCreate(BaseModel):
    title: str
    body: Optional[str] = None


class IssueOut(BaseModel):
    id: int
    repo_id: int
    author_id: int
    author_username: str
    title: str
    body: Optional[str]
    status: str
    created_at: datetime
