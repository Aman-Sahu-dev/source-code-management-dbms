"""Commit management."""

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg import AsyncConnection

from server.auth import validate_token
from server.database import get_db
from server.models import CommitCreate, CommitOut

router = APIRouter(tags=["commits"])


def _get_current_user(x_token: str | None = Header(default=None)):
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing X-Token header")
    username = validate_token(x_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


async def _get_user_id(username: str, db: AsyncConnection) -> int:
    row = await db.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = await row.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user[0]


async def _check_branch_access(repo_id: int, branch_id: int, user_id: int, db: AsyncConnection, min_role="viewer"):
    row = await db.execute(
        "SELECT role FROM collaborators WHERE repo_id = %s AND user_id = %s",
        (repo_id, user_id),
    )
    collab = await row.fetchone()
    if not collab:
        raise HTTPException(status_code=403, detail="Access denied")
    role_rank = {"viewer": 0, "developer": 1, "owner": 2}
    if role_rank.get(collab[0], -1) < role_rank.get(min_role, 0):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # Verify branch belongs to repo
    brow = await db.execute("SELECT id FROM branches WHERE id = %s AND repo_id = %s", (branch_id, repo_id))
    if not await brow.fetchone():
        raise HTTPException(status_code=404, detail="Branch not found in this repo")


@router.get("/repos/{repo_id}/branches/{branch_id}/commits", response_model=list[CommitOut])
async def list_commits(
    repo_id: int,
    branch_id: int,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    await _check_branch_access(repo_id, branch_id, user_id, db)
    rows = await db.execute(
        """
        SELECT c.id, c.branch_id, c.author_id, u.username, c.message, c.committed_at
        FROM commits c JOIN users u ON c.author_id = u.id
        WHERE c.branch_id = %s ORDER BY c.committed_at DESC
        """,
        (branch_id,),
    )
    return [
        CommitOut(id=r[0], branch_id=r[1], author_id=r[2], author_username=r[3], message=r[4], committed_at=r[5])
        for r in await rows.fetchall()
    ]


@router.post("/repos/{repo_id}/branches/{branch_id}/commits", response_model=CommitOut, status_code=201)
async def add_commit(
    repo_id: int,
    branch_id: int,
    body: CommitCreate,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    await _check_branch_access(repo_id, branch_id, user_id, db, min_role="developer")
    try:
        row = await db.execute(
            "INSERT INTO commits (branch_id, author_id, message) VALUES (%s, %s, %s) RETURNING id, committed_at",
            (branch_id, user_id, body.message),
        )
        c = await row.fetchone()
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return CommitOut(id=c[0], branch_id=branch_id, author_id=user_id, author_username=username, message=body.message, committed_at=c[1])
