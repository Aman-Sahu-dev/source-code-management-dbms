"""Branch management."""

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg import AsyncConnection

from server.auth import validate_token
from server.database import get_db
from server.models import BranchCreate, BranchOut

router = APIRouter(tags=["branches"])


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


async def _check_access(repo_id: int, user_id: int, db: AsyncConnection, min_role: str = "viewer"):
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
    return collab[0]


@router.get("/repos/{repo_id}/branches", response_model=list[BranchOut])
async def list_branches(
    repo_id: int,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    await _check_access(repo_id, user_id, db)
    rows = await db.execute(
        "SELECT id, repo_id, name, created_by, created_at FROM branches WHERE repo_id = %s ORDER BY created_at",
        (repo_id,),
    )
    return [BranchOut(id=r[0], repo_id=r[1], name=r[2], created_by=r[3], created_at=r[4])
            for r in await rows.fetchall()]


@router.post("/repos/{repo_id}/branches", response_model=BranchOut, status_code=201)
async def create_branch(
    repo_id: int,
    body: BranchCreate,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    await _check_access(repo_id, user_id, db, min_role="developer")
    try:
        row = await db.execute(
            "INSERT INTO branches (repo_id, name, created_by) VALUES (%s, %s, %s) RETURNING id, created_at",
            (repo_id, body.name, user_id),
        )
        b = await row.fetchone()
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return BranchOut(id=b[0], repo_id=repo_id, name=body.name, created_by=user_id, created_at=b[1])
