"""Repository CRUD."""

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg import AsyncConnection

from server.auth import validate_token
from server.database import get_db
from server.models import RepoCreate, RepoOut

router = APIRouter(prefix="/repos", tags=["repos"])


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


@router.get("", response_model=list[RepoOut])
async def list_repos(
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    rows = await db.execute(
        """
        SELECT rs.id, rs.name, rs.description, rs.is_private,
               rs.owner_id, rs.owner_username, rs.created_at,
               rs.commit_count, rs.open_issue_count
        FROM repo_summary rs
        WHERE rs.id IN (
            SELECT repo_id FROM collaborators WHERE user_id = %s
        )
        ORDER BY rs.created_at DESC
        """,
        (user_id,),
    )
    return [
        RepoOut(
            id=r[0], name=r[1], description=r[2], is_private=r[3],
            owner_id=r[4], owner_username=r[5], created_at=r[6],
            commit_count=r[7], open_issue_count=r[8],
        )
        for r in await rows.fetchall()
    ]


@router.post("", response_model=RepoOut, status_code=201)
async def create_repo(
    body: RepoCreate,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    try:
        row = await db.execute(
            """
            INSERT INTO repositories (name, description, owner_id, is_private)
            VALUES (%s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (body.name, body.description, user_id, body.is_private),
        )
        repo = await row.fetchone()
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return RepoOut(
        id=repo[0], name=body.name, description=body.description,
        is_private=body.is_private, owner_id=user_id, owner_username=username,
        created_at=repo[1], commit_count=0, open_issue_count=0,
    )


@router.get("/{repo_id}", response_model=RepoOut)
async def get_repo(
    repo_id: int,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    # Check access
    access = await db.execute(
        "SELECT 1 FROM collaborators WHERE repo_id = %s AND user_id = %s",
        (repo_id, user_id),
    )
    if not await access.fetchone():
        raise HTTPException(status_code=403, detail="Access denied")
    row = await db.execute(
        """
        SELECT id, name, description, is_private, owner_id, owner_username,
               created_at, commit_count, open_issue_count
        FROM repo_summary WHERE id = %s
        """,
        (repo_id,),
    )
    r = await row.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepoOut(
        id=r[0], name=r[1], description=r[2], is_private=r[3],
        owner_id=r[4], owner_username=r[5], created_at=r[6],
        commit_count=r[7], open_issue_count=r[8],
    )


@router.delete("/{repo_id}", status_code=204)
async def delete_repo(
    repo_id: int,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    # Only owner can delete
    row = await db.execute(
        "SELECT owner_id FROM repositories WHERE id = %s", (repo_id,)
    )
    repo = await row.fetchone()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo[0] != user_id:
        raise HTTPException(status_code=403, detail="Only the owner can delete a repository")
    try:
        # Transaction: delete cascades branches, commits, issues via FK
        await db.execute("DELETE FROM repositories WHERE id = %s", (repo_id,))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
